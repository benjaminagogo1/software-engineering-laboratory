import os

# Set before app.api is imported, because config reads the environment once at
# import time and minting a token without a secret raises. A fresh clone has no
# .env (it is gitignored), so without this the suite fails for a reason that has
# nothing to do with the code under test.
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")

# The session cookie is Secure in production, and a Secure cookie is never sent
# back over the plain http the test client speaks — so the whole cookie path
# would be invisible to the suite with the default left on.
os.environ.setdefault("COOKIE_SECURE", "false")

import pytest
from fastapi.testclient import TestClient

from app.api import (
    AuthLimits,
    app,
    get_audit_repository,
    get_auth_limits,
    get_service,
    get_user_service,
)
from app.models.user import User
from app.repositories.memory_audit_repository import MemoryAuditRepository
from app.repositories.sqlite_audit_repository import SqliteAuditRepository
from app.repositories.sqlite_expense_repository import SqliteExpenseRepository
from app.repositories.sqlite_user_repository import SqliteUserRepository
from app.services.expense_service import ExpenseService
from app.services.user_service import UserService


TEST_USERNAME = "api_user"
TEST_PASSWORD = "TestPassword123"


@pytest.fixture
def db_path(tmp_path):
    """A throwaway database per test, so nothing touches data/expense.db."""
    return tmp_path / "test_expense.db"


@pytest.fixture
def repositories(db_path):
    """
    Both repositories over the same file: an expense's user_id is a foreign
    key, so a registered user and their expenses have to share one database.
    """
    return (
        SqliteExpenseRepository(db_path),
        SqliteUserRepository(db_path),
    )


@pytest.fixture
def audit_repository():
    """
    The trail in a list, so a service test can assert on what was recorded
    without a second database in the way.

    Deliberately not the SQLite one: a test for "was this event recorded"
    should fail because the service did not record it, not because the trail
    table was somewhere else. The SQLite repository has its own tests, and the
    contract both must satisfy is asserted against each of them separately.
    """
    return MemoryAuditRepository()


@pytest.fixture
def sqlite_audit_repository(db_path):
    """The real trail, over the per-test database."""
    return SqliteAuditRepository(db_path, source="test")


@pytest.fixture
def expense_service(repositories, audit_repository):
    expense_repository, _ = repositories
    return ExpenseService(expense_repository, audit_repository)


@pytest.fixture
def user_service(repositories, audit_repository):
    _, user_repository = repositories
    return UserService(user_repository, audit_repository)


@pytest.fixture
def owner_id(repositories):
    """A user that repository-level tests can attach expenses to."""
    _, user_repository = repositories
    user = User(None, "owner", "test-password-hash")
    user_repository.add(user)
    return user.id


@pytest.fixture
def other_user_id(repositories):
    """
    A second user, for proving data is scoped per owner. It has to be a real
    row: expenses.user_id is a foreign key, so a made-up id would be rejected.
    """
    _, user_repository = repositories
    user = User(None, "other", "test-password-hash")
    user_repository.add(user)
    return user.id


@pytest.fixture
def client(expense_service, user_service, audit_repository):
    """
    Overrides every dependency that reaches a repository. get_user_service
    matters as much as get_service: without it /register and /login would reach
    for the real database that app.api builds at import time. get_audit_repository
    is the same story for /audit, and it is worse there — the route is a read of
    somebody's history, so a missing override would not fail, it would answer.

    get_auth_limits is overridden for a different reason — the real one is a
    module-level singleton holding failure counts, so a suite that logs in
    hundreds of times would trip its own rate limit and start seeing 429s from
    tests that have nothing to do with throttling. A fresh one per test means
    throttle tests get a limiter they own and every other test gets a clean one.
    """
    app.dependency_overrides[get_service] = lambda: expense_service
    app.dependency_overrides[get_user_service] = lambda: user_service
    app.dependency_overrides[get_auth_limits] = lambda: AuthLimits()
    app.dependency_overrides[get_audit_repository] = lambda: audit_repository

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers_for(client):
    """
    Registers and logs in an arbitrary username for real, so the auth path
    itself is exercised rather than a token being forged.

    Each test gets its own database, so usernames don't collide between tests.
    """
    def _auth_headers_for(username):
        credentials = {"username": username, "password": TEST_PASSWORD}

        register = client.post("/register", json=credentials)
        assert register.status_code == 201

        login = client.post("/login", json=credentials)
        assert login.status_code == 200

        token = login.json()["access_token"]

        return {"Authorization": f"Bearer {token}"}

    return _auth_headers_for


@pytest.fixture
def auth_headers(auth_headers_for):
    return auth_headers_for(TEST_USERNAME)


@pytest.fixture
def session_client(expense_service, user_service, audit_repository):
    """
    A client that behaves like a browser: it keeps cookies across requests, so
    the session cookie /login set is presented on the next call.

    Overrides the same dependencies as `client` — using both in one test is
    fine, but whichever tears down first clears them for both.
    """
    app.dependency_overrides[get_service] = lambda: expense_service
    app.dependency_overrides[get_user_service] = lambda: user_service
    app.dependency_overrides[get_auth_limits] = lambda: AuthLimits()
    app.dependency_overrides[get_audit_repository] = lambda: audit_repository

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def browser_session(session_client):
    """
    Registers and logs a user in through the real endpoints, and returns the
    CSRF token the server issued.

    Nothing is forged: the cookie on the client and the token returned here are
    the ones a browser would really be holding.
    """
    credentials = {"username": "browser_user", "password": TEST_PASSWORD}

    assert session_client.post("/register", json=credentials).status_code == 201

    login = session_client.post("/login", json=credentials)
    assert login.status_code == 200

    return login.json()["csrf_token"]

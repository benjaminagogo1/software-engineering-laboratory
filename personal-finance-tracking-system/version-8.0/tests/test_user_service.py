from app.auth.jwt import verify_token
from app.models.audit_event import (
    LOGIN_FAILED,
    LOGIN_SUCCEEDED,
    LOGOUT,
    USER_REGISTERED,
)
from app.repositories.memory_audit_repository import MemoryAuditRepository
from app.services.user_service import UserService


class FakeUserRepository:
    def __init__(self):
        self.users = []

    def find_by_username(self, username):
        for user in self.users:
            if user.username == username:
                return user
        return None

    def add(self, user):
        user.id = len(self.users) + 1
        self.users.append(user)


def test_register_user():
    repository = FakeUserRepository()
    service = UserService(repository, MemoryAuditRepository())

    user = service.register_user(
        "benjamin",
        "TestPassword123"
    )
    assert user is not None
    assert user.id == 1
    assert user.username == "benjamin"
    assert user.password_hash.startswith("$argon2id$")


def test_register_user_rejects_a_taken_username():
    repository = FakeUserRepository()
    service = UserService(repository, MemoryAuditRepository())

    service.register_user("benjamin", "TestPassword123")

    assert service.register_user("benjamin", "AnotherPassword456") is None


def test_authenticate_returns_the_matching_user():
    repository = FakeUserRepository()
    service = UserService(repository, MemoryAuditRepository())

    registered = service.register_user("benjamin", "TestPassword123")

    user = service.authenticate("benjamin", "TestPassword123")

    assert user is registered


def test_authenticate_with_a_wrong_password():
    repository = FakeUserRepository()
    service = UserService(repository, MemoryAuditRepository())

    service.register_user("benjamin", "TestPassword123")

    assert service.authenticate("benjamin", "wrong-password") is None


def test_authenticate_with_an_unknown_username():
    repository = FakeUserRepository()
    service = UserService(repository, MemoryAuditRepository())

    assert service.authenticate("nobody", "TestPassword123") is None


def test_login_mints_both_tokens_and_a_csrf_token():
    repository = FakeUserRepository()
    service = UserService(repository, MemoryAuditRepository())

    service.register_user("benjamin", "TestPassword123")

    tokens = service.login("benjamin", "TestPassword123")

    assert tokens is not None
    assert tokens.access_token
    assert tokens.session_token
    assert tokens.csrf_token

    # Distinct credentials: the browser's session and an API client's access
    # token must never be the same string, or one could stand in for the other.
    assert tokens.access_token != tokens.session_token

    # The CSRF token has to be inside the session it belongs to, since that is
    # what makes the double-submit check stateless.
    payload = verify_token(tokens.session_token)
    assert payload is not None
    assert payload["csrf"] == tokens.csrf_token

    # And the session has to be the longer-lived of the two.
    access = verify_token(tokens.access_token)
    assert access is not None
    assert payload["exp"] > access["exp"]


def test_login_with_a_wrong_password():
    repository = FakeUserRepository()
    service = UserService(repository, MemoryAuditRepository())

    service.register_user("benjamin", "TestPassword123")

    assert service.login("benjamin", "wrong-password") is None



# --- the audit trail ---------------------------------------------------------


def build_audited_service():
    """A service whose trail the test can read back."""
    repository = FakeUserRepository()
    return repository, UserService(repository, MemoryAuditRepository())


def test_registering_records_the_user():
    repository, service = build_audited_service()

    user = service.register_user("benjamin", "TestPassword123")

    assert service.audit.actions() == [USER_REGISTERED]

    recorded = service.audit.events[0]
    assert recorded.user_id == user.id
    assert recorded.entity_type == "user"
    assert recorded.detail == {"username": "benjamin"}


def test_a_rejected_registration_records_nothing():
    repository, service = build_audited_service()

    service.register_user("benjamin", "TestPassword123")
    service.audit.events.clear()

    assert service.register_user("benjamin", "AnotherPassword456") is None

    assert service.audit.actions() == []


def test_logging_in_records_it_once():
    """
    Once, not twice. login() delegates to authenticate(), which records — and
    if login() recorded again, every browser login would leave two rows saying
    the same thing, which is how a trail becomes unreadable.
    """
    repository, service = build_audited_service()

    service.register_user("benjamin", "TestPassword123")
    service.audit.events.clear()

    service.login("benjamin", "TestPassword123")

    assert service.audit.actions() == [LOGIN_SUCCEEDED]


def test_authenticating_directly_records_it_too():
    """
    The terminal client calls authenticate() and never touches login(), so if
    only login() were audited the CLI would be an unaudited way into an
    account — which is the whole reason the trail lives at this layer.
    """
    repository, service = build_audited_service()

    service.register_user("benjamin", "TestPassword123")
    service.audit.events.clear()

    service.authenticate("benjamin", "TestPassword123")

    assert service.audit.actions() == [LOGIN_SUCCEEDED]


def test_a_wrong_password_is_recorded_against_the_account():
    repository, service = build_audited_service()

    user = service.register_user("benjamin", "TestPassword123")
    service.audit.events.clear()

    assert service.login("benjamin", "wrong-password") is None

    assert service.audit.actions() == [LOGIN_FAILED]

    recorded = service.audit.events[0]
    assert recorded.user_id == user.id
    assert recorded.detail == {"username": "benjamin", "reason": "wrong password"}


def test_an_unknown_username_is_recorded_without_an_account():
    """
    No user_id, because there is no user. Attributing the attempt to whichever
    account happens to exist would put someone else's attack on your trail, and
    the username tried is the only real information there is.
    """
    repository, service = build_audited_service()

    assert service.authenticate("nobody", "TestPassword123") is None

    assert service.audit.actions() == [LOGIN_FAILED]

    recorded = service.audit.events[0]
    assert recorded.user_id is None
    assert recorded.detail == {"username": "nobody", "reason": "no such user"}


def test_the_password_never_reaches_the_trail():
    """
    The one thing an audit trail must never contain. This asserts it over the
    serialized form of every field rather than over detail alone, because the
    password could leak into a field that does not exist yet.
    """
    repository, service = build_audited_service()

    password = "CorrectHorseBatteryStaple"

    service.register_user("benjamin", password)
    service.authenticate("benjamin", password)
    service.authenticate("benjamin", "wrong-password")

    for recorded in service.audit.events:
        assert password not in str(recorded.detail)
        assert password not in recorded.detail_json()
        assert password not in recorded.action


def test_logging_out_is_recorded():
    """
    The one durable consequence of a logout — the token is stateless and the
    cookie is cleared by the API, so nothing else remembers it happened.
    """
    repository, service = build_audited_service()

    user = service.register_user("benjamin", "TestPassword123")
    service.audit.events.clear()

    service.logout(user.id)

    assert service.audit.actions() == [LOGOUT]
    assert service.audit.events[0].user_id == user.id

"""
`GET /audit` — the trail as the person it describes can read it.

The route exists for one question a user can legitimately ask about their own
account: what has been done with it, and from where. Most of what follows is
about the boundary rather than the happy path, because the trail holds every
user's rows in one table and the only thing standing between an account and
every other account's history is the route refusing to take a user id.
"""

import pytest

from app.models.audit_event import (
    EXPENSE_CREATED,
    EXPENSE_DELETED,
    LOGIN_FAILED,
    LOGIN_SUCCEEDED,
    USER_REGISTERED,
)
from tests.test_api import create_expense


AUDIT_PATH = "/audit"


def actions(body):
    """The action of every event in a decoded response, in the order returned."""
    return [event["action"] for event in body]


class TestWhoMayRead:
    def test_an_anonymous_request_is_refused(self, client):
        assert client.get(AUDIT_PATH).status_code == 401

    def test_a_bearer_token_is_enough(self, client, auth_headers):
        assert client.get(AUDIT_PATH, headers=auth_headers).status_code == 200

    def test_a_read_needs_no_csrf_token(self, client, auth_headers):
        # The CSRF guard is on mutations only, and a bearer caller would be
        # exempt anyway. Asserted rather than assumed, because putting the guard
        # on a read would break the browser client the moment it loaded.
        response = client.get(AUDIT_PATH, headers=auth_headers)

        assert "X-CSRF-Token" not in response.request.headers

    def test_the_cookie_session_can_read_it(self, session_client, browser_session):
        # The path the browser actually takes: the SPA holds a cookie and an
        # in-memory CSRF token, and a GET carries neither header.
        assert session_client.get(AUDIT_PATH).status_code == 200

    def test_an_invalid_token_is_refused(self, client):
        response = client.get(AUDIT_PATH, headers={"Authorization": "Bearer nonsense"})

        assert response.status_code == 401


class TestWhatItReturns:
    def test_it_names_the_root_of_the_wire_schema(self, client, auth_headers):
        body = client.get(AUDIT_PATH, headers=auth_headers).json()

        assert isinstance(body, list)

        keys = set(body[-1])

        assert keys == {
            "id",
            "happened_at",
            "action",
            "entity_type",
            "entity_id",
            "detail",
            "source",
        }

    def test_a_fresh_account_can_see_its_own_registration(self, client, auth_headers):
        body = client.get(AUDIT_PATH, headers=auth_headers).json()

        # Last, not first: the registration is the oldest thing this account did.
        assert actions(body)[-1] == USER_REGISTERED

    def test_it_is_newest_first(self, client, auth_headers):
        create_expense(client, auth_headers, name="Groceries", amount=24500)
        create_expense(client, auth_headers, name="Rent", amount=45000)

        body = client.get(AUDIT_PATH, headers=auth_headers).json()

        # The login is the oldest thing this account did, so it comes last; the
        # most recent expense is first.
        assert body[0]["action"] == EXPENSE_CREATED
        assert body[0]["detail"]["name"] == "Rent"
        assert body[-1]["action"] == USER_REGISTERED

    def test_the_events_are_in_order_of_the_ids(self, client, auth_headers):
        create_expense(client, auth_headers, name="Groceries")
        create_expense(client, auth_headers, name="Rent")

        body = client.get(AUDIT_PATH, headers=auth_headers).json()
        ids = [event["id"] for event in body]

        assert ids == sorted(ids, reverse=True)

    def test_an_expense_is_reconstructible_from_its_row(self, client, auth_headers):
        created = create_expense(client, auth_headers, name="Rent", amount=45000)
        expense_id = created.json()["expense"]["id"]

        client.delete(f"/expenses/{expense_id}", headers=auth_headers)

        deletion = client.get(AUDIT_PATH, headers=auth_headers).json()[0]

        assert deletion["action"] == EXPENSE_DELETED
        assert deletion["entity_type"] == "expense"
        assert deletion["entity_id"] == expense_id
        # The whole row was snapshotted before the DELETE, so the trail can still
        # say what was destroyed after the row itself is gone.
        assert deletion["detail"]["name"] == "Rent"
        assert deletion["detail"]["amount"] == 45000

    def test_the_source_is_carried_through(self, client, auth_headers):
        # The test repository stamps its own source, so the value is the
        # fixture's — what is asserted is that the route passes the column
        # through rather than dropping it, since "which surface did this" is the
        # question the field is there to answer.
        body = client.get(AUDIT_PATH, headers=auth_headers).json()

        assert body[0]["source"] is not None


class TestTheLimit:
    def test_the_default_is_a_cap_and_not_merely_a_default(self, client, auth_headers):
        # Sixty rows in the trail, fifty returned. An unbounded default would
        # turn the first page load of a long-lived account into a full table
        # read, which is a performance problem the client cannot even see.
        for index in range(58):
            create_expense(client, auth_headers, name=f"Expense {index}")

        body = client.get(AUDIT_PATH, headers=auth_headers).json()

        assert len(body) == 50

    def test_it_can_be_narrowed(self, client, auth_headers):
        create_expense(client, auth_headers, name="Groceries")
        create_expense(client, auth_headers, name="Rent")

        body = client.get(f"{AUDIT_PATH}?limit=1", headers=auth_headers).json()

        assert len(body) == 1
        # Narrowed from the newest end, not the oldest: the interesting rows are
        # always the recent ones.
        assert body[0]["detail"]["name"] == "Rent"

    @pytest.mark.parametrize("limit", [0, -1, 201, 10_000])
    def test_a_limit_outside_the_bound_is_a_422(self, client, auth_headers, limit):
        # Capped rather than clamped: a client asking for a hundred thousand
        # rows has a bug, and silently returning a different number than it
        # asked for hides it.
        response = client.get(f"{AUDIT_PATH}?limit={limit}", headers=auth_headers)

        assert response.status_code == 422

    def test_a_non_numeric_limit_is_a_422(self, client, auth_headers):
        response = client.get(f"{AUDIT_PATH}?limit=many", headers=auth_headers)

        assert response.status_code == 422

    def test_the_boundaries_are_accepted(self, client, auth_headers):
        assert client.get(f"{AUDIT_PATH}?limit=1", headers=auth_headers).status_code == 200
        assert client.get(f"{AUDIT_PATH}?limit=200", headers=auth_headers).status_code == 200


class TestItShowsOnlyTheCaller:
    def test_one_account_cannot_read_another(self, client, auth_headers_for):
        """
        The property the whole route rests on. Both accounts are in one table;
        the route takes no user id, so there is nothing to tamper with.
        """
        ben = auth_headers_for("benjamin")
        other = auth_headers_for("other_user")

        create_expense(client, ben, name="Mine", amount=100)
        create_expense(client, other, name="Theirs", amount=900)

        names = [
            event["detail"]["name"]
            for event in client.get(AUDIT_PATH, headers=ben).json()
            if event["action"] == EXPENSE_CREATED
        ]

        assert names == ["Mine"]

    def test_a_user_id_cannot_be_supplied(self, client, auth_headers_for):
        # Not rejected — ignored. The parameter does not exist, so FastAPI drops
        # it, which is a stronger guarantee than validating one: there is no
        # code path that could be talked into honouring it.
        ben = auth_headers_for("benjamin")
        other = auth_headers_for("other_user")

        create_expense(client, other, name="Theirs")

        body = client.get(f"{AUDIT_PATH}?user_id=2", headers=ben).json()

        # Newest first, so the login comes before the registration.
        assert actions(body) == [LOGIN_SUCCEEDED, USER_REGISTERED]

    def test_each_account_sees_only_its_own_logins(self, client, auth_headers_for):
        ben = auth_headers_for("benjamin")
        auth_headers_for("other_user")

        assert client.get(AUDIT_PATH, headers=ben).json()[0]["action"] == LOGIN_SUCCEEDED

        ben_ids = {event["id"] for event in client.get(AUDIT_PATH, headers=ben).json()}

        assert len(ben_ids) == 2


class TestGuessingIsVisibleToTheGuessed:
    def test_a_failed_login_against_your_account_is_in_your_trail(
        self, client, auth_headers
    ):
        """
        The point of recording a failure against the account rather than against
        the address. A run of these in your own history is what someone working
        through your password looks like from the inside — and it is the only
        way the person being attacked would ever find out.
        """
        client.post("/login", json={"username": "api_user", "password": "wrong-pass"})

        body = client.get(AUDIT_PATH, headers=auth_headers).json()

        assert body[0]["action"] == LOGIN_FAILED
        assert body[0]["detail"]["reason"] == "wrong password"
        # The username that was tried, which is the same one because the account
        # exists — pass-through, not a lookup.
        assert body[0]["detail"]["username"] == "api_user"

    def test_the_password_never_appears_in_the_trail(self, client, auth_headers):
        client.post("/login", json={"username": "api_user", "password": "hunter2-but-longer"})

        body = client.get(AUDIT_PATH, headers=auth_headers).json()

        assert "hunter2-but-longer" not in str(body)

    def test_a_failed_login_against_nobody_is_on_no_one_s_trail(
        self, client, auth_headers_for
    ):
        # No account to attribute it to. It is recorded — the username is worth
        # having — but `for_user` cannot return it, and should not: it is not an
        # event about any user of this application.
        ben = auth_headers_for("benjamin")

        client.post("/login", json={"username": "nobody", "password": "wrong-pass"})

        body = client.get(AUDIT_PATH, headers=ben).json()

        assert LOGIN_FAILED not in actions(body)

    def test_a_successful_login_after_failures_is_recorded_too(self, client, auth_headers):
        # Both halves, so the trail can answer "did they get in?" and not merely
        # "someone was trying".
        client.post("/login", json={"username": "api_user", "password": "wrong-pass"})
        client.post("/login", json={"username": "api_user", "password": "TestPassword123"})

        body = client.get(AUDIT_PATH, headers=auth_headers).json()

        assert [event["action"] for event in body[:2]] == [LOGIN_SUCCEEDED, LOGIN_FAILED]


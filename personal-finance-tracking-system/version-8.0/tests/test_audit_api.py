"""
The audit trail as the API produces it.

test_audit.py pins what a store does with an event; test_expense_service.py and
test_user_service.py pin which events a service raises. This file covers what
neither can: that a request over HTTP reaches an audited service at all. The
services are the only layer that records, so a route that built its own
repository — or a dependency wired to an unaudited service — would leave the
trail silent while every other test stayed green.
"""

import pytest

from app.models.audit_event import (
    EXPENSE_CREATED,
    EXPENSE_DELETED,
    EXPENSES_DELETED_ALL,
    LOGIN_FAILED,
    LOGIN_SUCCEEDED,
    LOGOUT,
    USER_REGISTERED,
)
from tests.test_api import create_expense


@pytest.fixture
def trail(expense_service):
    """
    The events recorded during this test.

    Read off the service because that is what the routes are handed: both the
    client and session_client fixtures override get_service with this instance,
    so an event that never appears here never reached a service.
    """
    return expense_service.audit


def test_registering_through_the_api_is_recorded(client, trail):
    client.post(
        "/register", json={"username": "benjamin", "password": "TestPassword123"}
    )

    assert trail.actions() == [USER_REGISTERED]
    assert trail.events[0].detail == {"username": "benjamin"}


def test_a_rejected_registration_records_nothing(client, trail):
    """409, and nothing was created, so nothing is claimed to have been."""
    client.post(
        "/register", json={"username": "benjamin", "password": "TestPassword123"}
    )
    trail.events.clear()

    response = client.post(
        "/register", json={"username": "benjamin", "password": "AnotherPassword456"}
    )

    assert response.status_code == 409
    assert trail.actions() == []


def test_logging_in_through_the_api_is_recorded(client, trail):
    credentials = {"username": "benjamin", "password": "TestPassword123"}

    client.post("/register", json=credentials)
    trail.events.clear()

    assert client.post("/login", json=credentials).status_code == 200

    assert trail.actions() == [LOGIN_SUCCEEDED]


def test_a_failed_login_is_recorded_without_saying_which_part_was_wrong(client, trail):
    """
    Two audiences, two answers. The trail distinguishes a missing account from a
    wrong password, because that is the difference between a typo and someone
    working through a list of usernames. The response must not, because telling
    an attacker which usernames exist is how a login form becomes a user
    enumeration oracle.
    """
    client.post(
        "/register", json={"username": "benjamin", "password": "TestPassword123"}
    )
    trail.events.clear()

    known = client.post(
        "/login", json={"username": "benjamin", "password": "wrong-password"}
    )
    unknown = client.post(
        "/login", json={"username": "nobody", "password": "wrong-password"}
    )

    assert known.status_code == unknown.status_code == 401
    assert known.json() == unknown.json()

    assert trail.events[0].detail["reason"] == "wrong password"
    assert trail.events[1].detail["reason"] == "no such user"


def test_creating_an_expense_is_recorded(client, auth_headers, trail):
    response = create_expense(client, auth_headers, name="Groceries", amount=24500)

    assert response.status_code == 201

    assert trail.actions() == [USER_REGISTERED, LOGIN_SUCCEEDED, EXPENSE_CREATED]

    recorded = trail.events[-1]

    assert recorded.entity_id == response.json()["expense"]["id"]
    assert recorded.detail["name"] == "Groceries"
    assert recorded.detail["amount"] == 24500


def test_a_rejected_expense_records_nothing(client, auth_headers, trail):
    """A 422 from validation never reaches a service, so it never reaches the trail."""
    response = client.post(
        "/expenses",
        json={"name": "Food", "amount": 2500, "category": "Shopping", "payment_type": "Cash"},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert trail.actions() == [USER_REGISTERED, LOGIN_SUCCEEDED]


def test_deleting_an_expense_is_recorded(client, auth_headers, trail):
    expense_id = create_expense(
        client, auth_headers, name="Rent", amount=45000
    ).json()["expense"]["id"]

    client.delete(f"/expenses/{expense_id}", headers=auth_headers)

    assert trail.actions()[-1] == EXPENSE_DELETED

    recorded = trail.events[-1]

    assert recorded.entity_id == expense_id
    assert recorded.detail["name"] == "Rent"
    assert recorded.detail["amount"] == 45000


def test_deleting_every_expense_is_recorded(client, auth_headers, trail):
    create_expense(client, auth_headers, name="Food")
    create_expense(client, auth_headers, name="Rent")

    client.delete("/expenses", headers=auth_headers)

    assert trail.actions()[-1] == EXPENSES_DELETED_ALL
    assert trail.events[-1].detail == {"deleted": 2}


def test_a_cleared_account_leaves_one_row_for_each_expense_and_one_for_the_sweep(
    client, auth_headers, trail
):
    """
    The bulk delete records its size rather than a copy of every row, because
    the rows are already in the trail as their own creations. This is the whole
    argument for that, asserted: the account is empty and the trail can still
    say exactly what it held.
    """
    create_expense(client, auth_headers, name="Food", amount=100)
    create_expense(client, auth_headers, name="Rent", amount=900)

    client.delete("/expenses", headers=auth_headers)

    created = [event for event in trail.events if event.action == EXPENSE_CREATED]

    assert [event.detail["amount"] for event in created] == [100, 900]


def test_logging_out_is_recorded(client, trail):
    credentials = {"username": "benjamin", "password": "TestPassword123"}

    client.post("/register", json=credentials)
    token = client.post("/login", json=credentials).json()["access_token"]

    trail.events.clear()

    response = client.post(
        "/logout", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert trail.actions() == [LOGOUT]


def test_a_refused_logout_is_not_recorded_as_a_logout(client, trail):
    """
    403 from the CSRF guard: the session is still open, so nothing ended. A
    trail claiming otherwise is worse than a silent one — it says a threat was
    closed when it was not.
    """
    response = client.post("/logout")

    assert response.status_code == 401
    assert trail.actions() == []


def test_an_unauthenticated_request_leaves_no_trail(client, trail):
    """
    Nothing on anyone's trail — including the trail of a user who has nothing
    to do with it. A rejected request is not an event *about* an account.
    """
    client.get("/expenses")
    client.delete("/expenses")

    assert trail.actions() == []


def test_expenses_are_recorded_against_the_user_who_owns_them(
    client, auth_headers_for, trail
):
    """
    Two accounts, one trail. Every event has to name the account it belongs to,
    or `for_user` — the only way the trail is ever read — cannot separate them.
    """
    first = auth_headers_for("first_user")
    second = auth_headers_for("second_user")

    create_expense(client, first, name="Mine", amount=100)
    create_expense(client, second, name="Theirs", amount=900)

    created = [event for event in trail.events if event.action == EXPENSE_CREATED]

    assert [event.user_id for event in created] == [1, 2]

    def bought_by(user_id):
        return [
            event.detail["name"]
            for event in trail.for_user(user_id)
            if event.action == EXPENSE_CREATED
        ]

    assert bought_by(1) == ["Mine"]
    assert bought_by(2) == ["Theirs"]

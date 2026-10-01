"""
Tests for the browser session: the httpOnly cookie, and the CSRF rule that
guards the routes a cookie can authenticate.

The bearer path is covered by test_api.py; this file is about the second way in
and the way the two are kept from being interchangeable.
"""

import config
from app.auth.cookies import SESSION_COOKIE

from tests.conftest import TEST_PASSWORD


def login(session_client, username):
    credentials = {"username": username, "password": TEST_PASSWORD}

    register = session_client.post("/register", json=credentials)
    assert register.status_code == 201

    return session_client.post("/login", json=credentials)


def create_expense(session_client, headers=None, **extra):
    payload = {
        "name": "Food",
        "amount": 2500.0,
        "category": "Food",
        "payment_type": "Cash",
    }
    payload.update(extra)

    return session_client.post("/expenses", json=payload, headers=headers or {})


# --- The cookie on its own --------------------------------------------------


def test_the_cookie_alone_authenticates_a_read(session_client, browser_session):
    # No Authorization header anywhere in this test: the cookie set by /login
    # is the whole credential.
    assert session_client.get("/expenses").status_code == 200


def test_the_cookie_is_not_the_access_token(session_client):
    response = login(session_client, "cookie_user")

    assert SESSION_COOKIE in session_client.cookies

    assert session_client.cookies[SESSION_COOKIE] != response.json()["access_token"]


def test_the_session_cookie_is_locked_down(session_client, monkeypatch):
    monkeypatch.setattr(config, "COOKIE_SECURE", True)

    header = login(session_client, "cookie_user").headers["set-cookie"].lower()

    assert "httponly" in header
    assert "samesite=lax" in header
    assert "path=/" in header
    # Script on the page can never read it, and it is never sent over plain
    # http — the two attributes that make it a session rather than a token in
    # a variable.
    assert "secure" in header


def test_the_cookie_can_be_relaxed_for_local_development(session_client, monkeypatch):
    """Over http the Secure flag silently drops the cookie, so it is switchable."""
    monkeypatch.setattr(config, "COOKIE_SECURE", False)

    header = login(session_client, "cookie_user").headers["set-cookie"].lower()

    assert "httponly" in header
    assert "secure" not in header


def test_a_tampered_cookie_is_rejected(session_client, browser_session):
    session_client.cookies.set(SESSION_COOKIE, "not-a-real-token")

    assert session_client.get("/expenses").status_code == 401


def test_no_credential_at_all_is_rejected(session_client):
    assert session_client.get("/expenses").status_code == 401


# --- /me, the boot check ----------------------------------------------------


def test_me_names_the_signed_in_user(session_client, browser_session):
    response = session_client.get("/me")

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "username": "browser_user",
        # Handed back so a page reload can carry on writing: the client holds
        # this in memory only.
        "csrf_token": browser_session,
    }


def test_me_gives_a_bearer_caller_no_csrf_token(client, auth_headers):
    """Nothing to hand back: a header-authenticated request cannot be forged."""
    response = client.get("/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["csrf_token"] is None


def test_me_without_a_session_is_unauthorized(session_client):
    assert session_client.get("/me").status_code == 401


# --- CSRF -------------------------------------------------------------------


def test_a_cookie_authenticated_write_needs_the_csrf_token(session_client, browser_session):
    response = create_expense(session_client)

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing CSRF token"


def test_a_wrong_csrf_token_is_rejected(session_client, browser_session):
    response = create_expense(session_client, headers={"X-CSRF-Token": "guessed"})

    assert response.status_code == 403

    # And nothing was written on the way through.
    assert session_client.get("/expenses").json() == []


def test_the_csrf_token_has_to_belong_to_the_current_session(session_client):
    """
    Two logins in a row: the second replaces the cookie, so the first login's
    CSRF token must stop working. Otherwise a token would be a skeleton key
    rather than a property of one session.
    """
    credentials = {"username": "cookie_user", "password": TEST_PASSWORD}
    session_client.post("/register", json=credentials)

    first = session_client.post("/login", json=credentials).json()["csrf_token"]
    second = session_client.post("/login", json=credentials).json()["csrf_token"]

    assert first != second

    assert create_expense(
        session_client, headers={"X-CSRF-Token": first}
    ).status_code == 403

    assert create_expense(
        session_client, headers={"X-CSRF-Token": second}
    ).status_code == 201


def test_a_cookie_authenticated_write_succeeds_with_the_csrf_token(
    session_client, browser_session
):
    response = create_expense(session_client, headers={"X-CSRF-Token": browser_session})

    assert response.status_code == 201
    assert response.json()["expense"]["name"] == "Food"


def test_every_mutating_route_is_guarded(session_client, browser_session):
    expense_id = create_expense(
        session_client, headers={"X-CSRF-Token": browser_session}
    ).json()["expense"]["id"]

    unguarded = [
        ("put", f"/expenses/{expense_id}", {"amount": 3000}),
        ("delete", f"/expenses/{expense_id}", None),
        ("delete", "/expenses", None),
        ("post", "/logout", None),
    ]

    for method, path, body in unguarded:
        send = getattr(session_client, method)

        # DELETE takes no body here, and httpx rejects a json= of None.
        response = send(path) if body is None else send(path, json=body)

        assert response.status_code == 403, f"{method.upper()} {path} was not guarded"

    # And the expense the guarded route was meant to touch is still there.
    assert session_client.get(f"/expenses/{expense_id}").status_code == 200


# --- The bearer path is untouched -------------------------------------------


def test_a_bearer_token_still_writes_without_a_csrf_token(client, auth_headers):
    """
    API clients keep working exactly as before: a forged cross-site request
    cannot carry an Authorization header, so there is nothing to counter-sign.
    """
    assert create_expense(client, headers=auth_headers).status_code == 201


def test_an_explicit_header_beats_an_ambient_cookie(
    session_client, browser_session, auth_headers_for
):
    """
    With both credentials present the header wins, so an API client is never
    silently downgraded to whoever happens to be logged in on the machine.
    """
    other = auth_headers_for("other_user")

    assert session_client.get("/me").json()["username"] == "browser_user"

    response = session_client.get("/me", headers=other)

    assert response.status_code == 200
    assert response.json()["username"] == "other_user"


# --- Logging out ------------------------------------------------------------


def test_logout_clears_the_session(session_client, browser_session):
    response = session_client.post(
        "/logout", headers={"X-CSRF-Token": browser_session}
    )

    assert response.status_code == 200
    assert SESSION_COOKIE not in session_client.cookies
    assert session_client.get("/expenses").status_code == 401


def test_logout_without_a_session_is_rejected(session_client):
    assert session_client.post("/logout").status_code == 401

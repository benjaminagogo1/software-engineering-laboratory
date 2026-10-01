"""
The auth routes' two new refusals, end to end through the API.

The counter itself is tested in tests/test_throttle.py and the rules in
tests/test_policy.py. What is checked here is the wiring: that the routes
consult the counters at all, that a refusal arrives as the right status code
with a usable Retry-After, and that the address a request is keyed on cannot be
chosen by the caller.
"""

import pytest

from app.api import AuthLimits, app, client_address, get_auth_limits
from app.auth.policy import MIN_LENGTH


# Long enough to clear the length rule and containing no username used below, so
# a failure in these tests is about the route and not about the policy.
GOOD_PASSWORD = "TestPassword123"


@pytest.fixture
def limits():
    """A limiter the test owns, so a threshold can be tightened without waiting."""
    return AuthLimits()


@pytest.fixture
def limited_client(client, limits):
    """
    The shared client, wired to a limiter this test can reach into.

    Overriding after the `client` fixture has already yielded is fine: the
    dependency is resolved per request, not per client.
    """
    app.dependency_overrides[get_auth_limits] = lambda: limits

    return client


def fail_login(client, username, password="not-the-password"):
    return client.post("/login", json={"username": username, "password": password})


class TestRegisterRefusesWeakCredentials:
    def test_a_short_password_is_a_400(self, client):
        response = client.post(
            "/register", json={"username": "someone", "password": "short"}
        )

        assert response.status_code == 400

    def test_the_body_carries_the_reason(self, client):
        # Not a generic "invalid". The policy returns a sentence so the form can
        # show it, and a route that swallowed it into "Bad Request" would waste
        # that — the person is the one who has to fix the input.
        response = client.post(
            "/register", json={"username": "someone", "password": "short"}
        )

        assert response.json()["detail"] == (
            f"Password must be at least {MIN_LENGTH} characters"
        )

    def test_a_common_password_is_a_400(self, client):
        response = client.post(
            "/register", json={"username": "someone", "password": "password1234"}
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Password is too common"

    def test_a_password_containing_the_username_is_a_400(self, client):
        response = client.post(
            "/register", json={"username": "benedict", "password": "benedict-benedict"}
        )

        assert response.status_code == 400

    def test_a_short_username_is_a_400(self, client):
        response = client.post(
            "/register", json={"username": "ab", "password": GOOD_PASSWORD}
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Username must be at least 3 characters"

    def test_a_username_with_a_space_is_a_400(self, client):
        response = client.post(
            "/register", json={"username": "ben jamin", "password": GOOD_PASSWORD}
        )

        assert response.status_code == 400

    def test_the_refused_username_is_not_created(self, client):
        # The policy runs before the lookup, so this is really asserting it runs
        # inside register_user and not merely at the route — a check that
        # happened after the insert would leave the row behind.
        client.post("/register", json={"username": "ab", "password": GOOD_PASSWORD})

        taken = client.post(
            "/register", json={"username": "ab", "password": GOOD_PASSWORD}
        )

        # Still 400 for the username, not 409 for a name that now exists.
        assert taken.status_code == 400

    def test_a_good_pair_is_still_created(self, client):
        response = client.post(
            "/register", json={"username": "someone", "password": GOOD_PASSWORD}
        )

        assert response.status_code == 201
        assert response.json()["username"] == "someone"

    def test_a_padded_username_is_stored_trimmed(self, client):
        # The rule is applied to the string that gets stored, so "  someone  "
        # and "someone" must be the same account rather than two.
        created = client.post(
            "/register", json={"username": "  someone  ", "password": GOOD_PASSWORD}
        )

        assert created.status_code == 201
        assert created.json()["username"] == "someone"

        duplicate = client.post(
            "/register", json={"username": "someone", "password": GOOD_PASSWORD}
        )

        assert duplicate.status_code == 409

    def test_a_taken_username_is_still_a_409(self, client):
        # The other half of the pair of outcomes: a name that exists is not the
        # same answer as input that was never acceptable.
        credentials = {"username": "api_user", "password": GOOD_PASSWORD}

        assert client.post("/register", json=credentials).status_code == 201
        assert client.post("/register", json=credentials).status_code == 409


class TestLoginRefusesAfterRepeatedFailures:
    def test_a_few_mistakes_are_not_throttled(self, limited_client):
        # A person who mistypes is not the threat model. Five failures are free,
        # so an honest run of them must not start refusing.
        limited_client.post(
            "/register", json={"username": "someone", "password": GOOD_PASSWORD}
        )

        for _ in range(5):
            assert fail_login(limited_client, "someone").status_code == 401

    def test_repeated_failures_eventually_get_a_429(self, limited_client):
        limited_client.post(
            "/register", json={"username": "someone", "password": GOOD_PASSWORD}
        )

        for _ in range(6):
            assert fail_login(limited_client, "someone").status_code == 401

        assert fail_login(limited_client, "someone").status_code == 429

    def test_the_refusal_carries_a_retry_after(self, limited_client):
        limited_client.post(
            "/register", json={"username": "someone", "password": GOOD_PASSWORD}
        )

        for _ in range(6):
            fail_login(limited_client, "someone")

        response = fail_login(limited_client, "someone")

        # Rounded up, and at least 1: a Retry-After of 0 invites an immediate
        # retry that is refused again, which reads as a broken server.
        assert int(response.headers["Retry-After"]) >= 1

    def test_the_body_says_what_happened(self, limited_client):
        limited_client.post(
            "/register", json={"username": "someone", "password": GOOD_PASSWORD}
        )

        for _ in range(6):
            fail_login(limited_client, "someone")

        assert fail_login(limited_client, "someone").json()["detail"] == (
            "Too many failed attempts. Try again later."
        )

    def test_the_refusal_happens_even_with_the_right_password(self, limited_client):
        # The counters are consulted before the credentials are, which is the
        # whole reason to throttle this route rather than only refuse at the
        # end: a throttled request must cost no argon2 verification.
        limited_client.post(
            "/register", json={"username": "someone", "password": GOOD_PASSWORD}
        )

        for _ in range(6):
            fail_login(limited_client, "someone")

        throttled = limited_client.post(
            "/login", json={"username": "someone", "password": GOOD_PASSWORD}
        )

        assert throttled.status_code == 429

    def test_a_success_clears_the_count(self, limited_client):
        limited_client.post(
            "/register", json={"username": "someone", "password": GOOD_PASSWORD}
        )

        for _ in range(5):
            fail_login(limited_client, "someone")

        assert limited_client.post(
            "/login", json={"username": "someone", "password": GOOD_PASSWORD}
        ).status_code == 200

        # Back to a clean slate: another five honest mistakes must not tip it
        # over, which is the difference between clearing and merely not adding.
        for _ in range(5):
            assert fail_login(limited_client, "someone").status_code == 401

        assert limited_client.post(
            "/login", json={"username": "someone", "password": GOOD_PASSWORD}
        ).status_code == 200

    def test_a_different_address_is_not_punished_for_this_one(
        self, limited_client, monkeypatch
    ):
        # The pair key includes the address precisely so that an attacker's
        # failures cannot lock the real user out of their own account. Same
        # username, different peer, so a different pair — and the second peer
        # gets its own five free mistakes.
        limited_client.post(
            "/register", json={"username": "someone", "password": GOOD_PASSWORD}
        )

        for _ in range(6):
            fail_login(limited_client, "someone")

        assert fail_login(limited_client, "someone").status_code == 429

        monkeypatch.setattr(
            "app.api.client_address", lambda request: "198.51.100.7"
        )

        assert fail_login(limited_client, "someone").status_code == 401


class TestRegisterIsLimitedByAddress:
    def test_repeated_registrations_eventually_get_a_429(self, limited_client, limits):
        limited_client.post(
            "/register", json={"username": "someone", "password": GOOD_PASSWORD}
        )

        # Every attempt counts here, refused or not, because what the route
        # spends is an argon2 hash and a row — and a request that succeeds
        # spends both.
        for index in range(20):
            response = limited_client.post(
                "/register",
                json={"username": f"person{index}", "password": GOOD_PASSWORD},
            )

            if response.status_code == 429:
                break
        else:
            pytest.fail("register never throttled")

        assert int(response.headers["Retry-After"]) >= 1


class TestTheAddressCannotBeChosen:
    def test_a_fabricated_forwarded_for_does_not_reset_the_limit(self, limited_client):
        # The bypass this closes: read X-Forwarded-For and every request can
        # present a different address, so every request is a fresh key and the
        # limiter never fires.
        limited_client.post(
            "/register", json={"username": "someone", "password": GOOD_PASSWORD}
        )

        for index in range(6):
            limited_client.post(
                "/login",
                json={"username": "someone", "password": "not-the-password"},
                headers={"X-Forwarded-For": f"203.0.113.{index}"},
            )

        throttled = limited_client.post(
            "/login",
            json={"username": "someone", "password": "not-the-password"},
            headers={"X-Forwarded-For": "203.0.113.99"},
        )

        assert throttled.status_code == 429


class TestClientAddress:
    class FakeRequest:
        def __init__(self, client, headers=None):
            self.client = client
            self.headers = headers or {}

    class Peer:
        def __init__(self, host):
            self.host = host

    def test_it_returns_the_peer(self):
        request = self.FakeRequest(self.Peer("198.51.100.7"))

        assert client_address(request) == "198.51.100.7"

    def test_it_ignores_forwarded_for(self):
        request = self.FakeRequest(
            self.Peer("198.51.100.7"), {"X-Forwarded-For": "203.0.113.9"}
        )

        assert client_address(request) == "198.51.100.7"

    def test_an_unattributable_request_shares_one_key(self):
        # A socket that has already gone, or a test transport. Falling over
        # would turn a limiter into an outage; sharing one key errs towards
        # throttling too much rather than not at all.
        request = self.FakeRequest(None)

        assert client_address(request) == "unknown"

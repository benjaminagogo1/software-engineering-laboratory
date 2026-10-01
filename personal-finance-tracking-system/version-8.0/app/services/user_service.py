from typing import NamedTuple

from app.auth import policy
from app.auth.jwt import create_access_token, create_session_token, new_csrf_token
from app.auth.password import hash_password, verify_password
from app.models.audit_event import (
    AuditEvent,
    LOGIN_FAILED,
    LOGIN_SUCCEEDED,
    LOGOUT,
    USER_REGISTERED,
)
from app.models.user import User
from app.services.audited_service import AuditedService


def normalize_username(username):
    """
    The one spelling of a username this application stores and looks up.

    Applied on both sides — registering and authenticating — because applying it
    to one and not the other creates the account nobody can log into: stored as
    "ben", looked up as "ben ". Normalizing at the boundary also means the policy
    judges the string that will actually be stored.
    """
    if not isinstance(username, str):
        return username

    return username.strip()


class LoginTokens(NamedTuple):
    """Everything a successful login hands back, before any transport is chosen."""

    access_token: str
    session_token: str
    csrf_token: str


class UserService(AuditedService):
    def __init__(self, repository, audit):
        super().__init__(audit)

        self.repository = repository

    def register_user(self, username, password):
        """
        Creates an account, or returns None when the username is taken.

        Raises WeakCredentials when the policy refuses the pair. Two different
        outcomes because they are two different answers: 409 Conflict for a name
        that exists, 400 Bad Request for input that was never acceptable — and
        because the check runs before any lookup, refusing bad input costs no
        database round trip.
        """
        username = normalize_username(username)

        policy.check(username, password)

        existing_user = self.repository.find_by_username(username)

        if existing_user is not None:
            return None

        password_hash = hash_password(password)

        user = User(None, username, password_hash)

        self.repository.add(user)

        # The id is only known after the insert, which is why this is recorded
        # here rather than anywhere the username is first seen.
        self._record(AuditEvent(
            action=USER_REGISTERED,
            user_id=user.id,
            entity_type="user",
            entity_id=user.id,
            detail={"username": username},
        ))

        return user

    def authenticate(self, username, password):
        """Returns the matching user, or None if the credentials are wrong.

        The CLI authenticates a local user without needing a token, so the
        credential check lives on its own and login() builds on it.

        Both outcomes are recorded here rather than in login(), because this is
        the one place every surface passes through. Auditing only login() would
        leave the terminal client — which calls this directly — as an unaudited
        way into an account, and the whole reason the trail lives at the service
        layer is that there should not be one.

        The attempted username is recorded and passed through as given: an
        account's trail showing the names tried against it is how a credential
        stuffer is noticed at all. The password never appears, and neither does
        anything derived from it.
        """
        username = normalize_username(username)

        user = self.repository.find_by_username(username)

        if user is None:
            self._record(AuditEvent(
                action=LOGIN_FAILED,
                user_id=None,
                detail={"username": username, "reason": "no such user"},
            ))

            return None

        if not verify_password(password, user.password_hash):
            # user_id set, unlike the branch above: the account exists, so this
            # is an attempt *on* it and belongs in its trail. The two reasons
            # are distinguished here and not in the API response, which stays
            # deliberately uniform — inside the trail the distinction is the
            # whole point, and nobody attacking from outside reads it.
            self._record(AuditEvent(
                action=LOGIN_FAILED,
                user_id=user.id,
                detail={"username": username, "reason": "wrong password"},
            ))

            return None

        self._record(AuditEvent(
            action=LOGIN_SUCCEEDED,
            user_id=user.id,
            detail={"username": username},
        ))

        return user

    def login(self, username, password):
        """
        Verifies the credentials and mints both tokens a session needs, or
        returns None when they are wrong.

        Both are minted here because both need the same verified user, but
        which one travels in an httpOnly cookie and which in the response body
        is the API layer's decision — this layer knows nothing about cookies.

        No audit row is written here. authenticate() already recorded this
        login, and recording it again would put two rows in the trail for one
        event.
        """
        user = self.authenticate(username, password)

        if user is None:
            return None

        csrf_token = new_csrf_token()

        return LoginTokens(
            access_token=create_access_token(user.id),
            session_token=create_session_token(user.id, csrf_token),
            csrf_token=csrf_token,
        )

    def logout(self, user_id):
        """
        Records that a session ended.

        There is no state to change: the session token is a stateless JWT, so
        the cookie is cleared by the API and the token itself stays valid until
        it expires. That makes the audit row the only durable consequence of a
        logout — which is a reason to have this method, not a reason it is
        empty. A trail that shows every login and no logouts cannot answer
        "was that session still open?".
        """
        self._record(AuditEvent(action=LOGOUT, user_id=user_id))


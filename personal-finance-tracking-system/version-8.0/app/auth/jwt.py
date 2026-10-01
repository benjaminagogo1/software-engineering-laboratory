import secrets
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError

import config


# Short on purpose: an API client that holds its own token can re-authenticate
# cheaply, so a leaked one is only useful for minutes.
ACCESS_TOKEN_TTL_MINUTES = 15

# What kind of caller a token was minted for. Both kinds are signed with the
# same secret and carry the same user_id, so without this claim they would be
# interchangeable — and the CSRF rule depends on telling them apart.
ACCESS_TOKEN = "access"
SESSION_TOKEN = "session"

ALGORITHM = "HS256"


def _encode(payload):
    return jwt.encode(payload, config.require_jwt_secret(), algorithm=ALGORITHM)


def create_access_token(user_id):
    """
    Mints a token for a client that stores it and presents it itself: curl, a
    mobile app, a service.

    It travels in an `Authorization: Bearer` header, which a cross-site
    attacker cannot set on a forged request, so requests authenticated this way
    need no CSRF counter-signature.
    """
    expiration_time = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_TTL_MINUTES
    )

    return _encode({
        "user_id": user_id,
        "typ": ACCESS_TOKEN,
        "exp": expiration_time,
    })


def create_session_token(user_id, csrf):
    """
    Mints the longer-lived token the browser carries in its httpOnly cookie.

    The csrf value rides inside the signed payload rather than in a
    server-side session store. Echoing it back in a header proves the caller
    could read a response from this origin, which is precisely what a
    cross-site forger cannot do — so the double-submit check stays stateless.
    """
    expiration_time = datetime.now(timezone.utc) + timedelta(
        hours=config.SESSION_TTL_HOURS
    )

    return _encode({
        "user_id": user_id,
        "typ": SESSION_TOKEN,
        "csrf": csrf,
        "exp": expiration_time,
    })


def new_csrf_token():
    """A fresh counter-signature for one login."""
    return secrets.token_urlsafe(32)


def verify_token(token):
    """
    Returns the token's payload, or None if it is malformed, tampered with or
    expired.

    Deliberately does not care which kind of token it is: every caller either
    accepts both or checks `typ` itself.
    """
    try:
        return jwt.decode(token, config.require_jwt_secret(), algorithms=[ALGORITHM])

    except InvalidTokenError:
        return None

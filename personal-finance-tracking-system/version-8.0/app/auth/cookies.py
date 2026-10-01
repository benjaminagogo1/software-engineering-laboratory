"""
The browser session cookie.

Set and clear live together because they have to agree: a cookie is identified
by its name, domain and path, so clearing it with a different path leaves the
browser still sending a cookie the server believes it deleted.
"""

import config


SESSION_COOKIE = "session"


def _attributes():
    return {
        "key": SESSION_COOKIE,
        "httponly": True,
        # Lax rather than Strict: a Strict cookie is withheld on a top-level
        # navigation into the app, so following a link to it would land on the
        # login screen while already logged in.
        "samesite": "lax",
        "secure": config.COOKIE_SECURE,
        "path": "/",
    }


def set_session_cookie(response, token):
    """
    Attaches the session to the response.

    max_age matches the token's own expiry, so the browser stops sending it at
    the same moment the server stops accepting it.
    """
    response.set_cookie(
        value=token,
        max_age=config.SESSION_TTL_HOURS * 3600,
        **_attributes(),
    )


def clear_session_cookie(response):
    """Expires the session cookie in the browser."""
    response.delete_cookie(**_attributes())

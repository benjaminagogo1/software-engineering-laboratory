"""
What an acceptable username and password are.

Deliberately **not** a composition rule. The reflex — one uppercase, one digit,
one symbol — is what NIST SP 800-63B §5.1.1.2 explicitly recommends against, and
the reasoning is in the guidance: composition rules push people towards
`Password1!`, which is short, predictable, and typed the same way on every
system they own. Length is the only requirement that reliably buys entropy, so
length is the requirement here.

Equally deliberately absent: password expiry and password history. Both are
named in the same section as practices to avoid. An expiry trains people to
increment a number.

The rules are here, in one module, rather than spread across the API schema and
the terminal prompt, because a rule that lives in two places is enforced in one
of them. `UserService.register_user` applies this; every surface inherits it.
"""


# NIST's floor is 8. The floor in this module is 12, because the floor is not
# the recommendation — it is the value below which a password is refused
# outright, and anyone choosing one is choosing from a search space a laptop
# walks through.
MIN_LENGTH = 12

# The one that is not about strength. Argon2 will hash a megabyte of input as
# happily as it hashes twelve characters, so an uncapped password field is a
# cheap way to make the server do expensive work — one request, one hash of
# whatever size the attacker chose. 128 is past every password manager's
# maximum and short of anything that matters computationally.
MAX_LENGTH = 128

# Usernames are stored, indexed and returned; nothing needs one longer than
# this, and the cap stops the column being used as free storage.
MAX_USERNAME_LENGTH = 64
MIN_USERNAME_LENGTH = 3


class WeakCredentials(ValueError):
    """
    A username or password the policy refuses.

    Raised rather than returned because it cannot be ignored. `register_user`
    already returns None for a taken username, and a second return value
    meaning "bad password" would be checked by whoever wrote the first caller
    and forgotten by whoever writes the third. Same reasoning as making the
    audit repository a required constructor argument.

    A ValueError because that is what it is — a bad argument — so a caller that
    does not catch it specifically still fails loudly instead of proceeding.
    """


# The passwords that show up at the top of every breach corpus. Short, because
# this is a shape check and not a breach lookup: it catches the handful someone
# actually reaches for, and it is honest about not being a substitute for
# checking against a real corpus. See the note at the bottom of this file.
COMMON_PASSWORDS = frozenset({
    "password1234",
    "passwordpassword",
    "qwertyuiop123",
    "123456789012",
    "111111111111",
    "iloveyou1234",
    "administrator1",
    "letmeinletmein",
    "welcome12345",
    "monkey123456",
    "dragon123456",
    "football1234",
    "baseball1234",
    "sunshine1234",
    "princess1234",
    "superman1234",
    "trustno1trustno1",
    "abcdefghijkl",
    "qwerty123456",
    "1qaz2wsx3edc",
    "zaq12wsxcde3",
    "letmein12345",
    "changeme1234",
    "passw0rdpassw0rd",
})


def password_problem(username, password):
    """
    Why this password is unacceptable, or None if it is fine.

    Returns the reason rather than a boolean so the caller has something to show
    the person: "that is too short" is actionable, "invalid" is not.

    `password` is never stripped or altered before being judged. NIST is
    explicit that leading and trailing spaces are valid characters and must be
    accepted and hashed as given — a password silently trimmed at registration
    and not at login is an account nobody can get into.
    """
    if not isinstance(password, str) or not password.strip():
        return "Password must not be empty"

    if len(password) < MIN_LENGTH:
        return f"Password must be at least {MIN_LENGTH} characters"

    if len(password) > MAX_LENGTH:
        return f"Password must be at most {MAX_LENGTH} characters"

    if password.lower() in COMMON_PASSWORDS:
        return "Password is too common"

    # Only worth checking against a username long enough to be recognisable
    # inside a password — "jo" appears in most words.
    if (
        isinstance(username, str)
        and len(username) >= MIN_USERNAME_LENGTH
        and username.lower() in password.lower()
    ):
        return "Password must not contain your username"

    return None


def username_problem(username):
    """Why this username is unacceptable, or None if it is fine."""
    if not isinstance(username, str) or not username.strip():
        return "Username must not be empty"

    # Measured before stripping, so a name that is real but padded is accepted
    # for what it is rather than refused for what it looked like.
    if len(username.strip()) < MIN_USERNAME_LENGTH:
        return f"Username must be at least {MIN_USERNAME_LENGTH} characters"

    if len(username) > MAX_USERNAME_LENGTH:
        return f"Username must be at most {MAX_USERNAME_LENGTH} characters"

    # Usernames are trimmed on the way in (see UserService.register_user), so a
    # name whose *interior* holds a newline or a tab would be stored with it.
    if any(character.isspace() for character in username.strip()):
        return "Username must not contain spaces"

    return None


def check(username, password):
    """
    Both rules, username first, raising on the first problem found.

    Order matters for the message and not for security: someone who typed a
    one-character username should be told about that rather than about a
    password they have not finished choosing.

    This runs before any database lookup on purpose — refusing bad input should
    not cost a round trip, and nothing about the answer depends on what is
    already stored.
    """
    problem = username_problem(username)

    if problem is None:
        problem = password_problem(username, password)

    if problem is not None:
        raise WeakCredentials(problem)


# What this does not do, stated here rather than discovered later: it does not
# check the password against a breach corpus. The real answer is a k-anonymity
# lookup against Have I Been Pwned's range API, which sends the first five
# characters of a SHA-1 hash and never the password. That is a network call on
# the registration path — a dependency, an outage mode, and a privacy question
# about a third party learning anything at all — so it is a deliberate decision
# to make rather than something to add by reflex.

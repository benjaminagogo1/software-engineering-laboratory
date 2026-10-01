import datetime
import json
from dataclasses import dataclass, field


# The actions worth recording. Constants rather than bare strings because
# these values are written to a table nobody prunes: a typo in a literal here
# is a permanent hole in the trail, and a typo in a constant does not run.
EXPENSE_CREATED = "expense.created"
EXPENSE_UPDATED = "expense.updated"
EXPENSE_DELETED = "expense.deleted"
EXPENSES_DELETED_ALL = "expenses.deleted_all"

USER_REGISTERED = "user.registered"
LOGIN_SUCCEEDED = "login.succeeded"
LOGIN_FAILED = "login.failed"
LOGOUT = "logout"


def now():
    """The current instant, as the string an audit row stores.

    UTC, always, with an explicit offset: an audit trail is read from a
    different timezone than it was written in more often than not, and a naive
    local timestamp is impossible to compare across rows once that happens.
    """
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


@dataclass
class AuditEvent:
    """
    One thing that happened, and who made it happen.

    Not the same thing as a log line, and not a duplicate of one. A log line is
    for whoever is running the software and is allowed to be dropped, sampled
    or rotated away. This is for whoever has to say, months later, who deleted
    which expense — so it is written to a table, in the same transaction-ready
    place as the data it describes, and never pruned by a level setting.

    `action` comes first rather than `id`, unlike Expense: the action is what
    the event *is*, and the id and timestamp are assigned by whoever stores it.

    `detail` holds whatever small, structured facts make the action
    reconstructible later — the deleted expense's amount, the changed fields,
    the username someone tried to log in with. It is stored as JSON, so it has
    to stay small and must never carry a password or a token.
    """

    action: str
    user_id: int | None = None
    entity_type: str | None = None
    entity_id: int | None = None
    detail: dict | None = None

    # Stamped by the store, which is the only layer that knows whether this
    # happened over HTTP or in the terminal.
    source: str | None = None
    happened_at: str = field(default_factory=now)
    id: int | None = None

    def detail_json(self):
        """`detail` as the text the column holds, or None when there is none."""
        if self.detail is None:
            return None

        # sort_keys so two rows describing the same edit are byte-identical,
        # which makes them diffable and lets a test assert on the string.
        return json.dumps(self.detail, sort_keys=True)

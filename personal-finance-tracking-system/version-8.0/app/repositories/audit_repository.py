from abc import ABC, abstractmethod


class AuditRepository(ABC):
    """
    Where the audit trail is kept.

    Two methods, deliberately: a trail is only trustworthy if nothing can
    rewrite it, so there is no update and no delete here. The absence is the
    feature — an interface with a `delete` on it invites a caller to tidy up
    the one row that mattered.
    """

    @abstractmethod
    def record(self, event):
        """
        Appends one event and returns it with its id and timestamp filled in.

        The source is stamped here rather than by the caller: the store is the
        only thing that knows which surface it belongs to, and a service that
        had to be told would be a service that could be told wrong.
        """

    @abstractmethod
    def for_user(self, user_id, limit=100):
        """The most recent events attributed to one user, newest first."""

from app.models.audit_event import AuditEvent
from app.repositories.audit_repository import AuditRepository


class MemoryAuditRepository(AuditRepository):
    """
    The audit trail held in a list.

    Exists for the same reason MemoryExpenseRepository does: a service test
    should be able to assert on what was recorded without a database in the
    way. It is also the honest answer to "where does the trail go" for a caller
    who genuinely wants it in memory — though for anything that will be asked
    to prove something later, the SQLite one is the reason this interface
    exists at all.
    """

    def __init__(self, source="memory"):
        self.source = source
        self.events: list[AuditEvent] = []
        self._next_id = 1

    def record(self, event):
        event.source = self.source
        event.id = self._next_id
        self._next_id += 1

        self.events.append(event)

        return event

    def for_user(self, user_id, limit=100):
        matching = [event for event in self.events if event.user_id == user_id]

        # Newest first, which for an append-only list is the end of it.
        return list(reversed(matching))[:limit]

    def actions(self):
        """Every recorded action name, oldest first. A test convenience."""
        return [event.action for event in self.events]

import json
import sqlite3

from app.models.audit_event import AuditEvent
from app.repositories.audit_repository import AuditRepository
from app.storage.sqlite_storage import SqliteStorage
from app.storage.storage_error import StorageError


class SqliteAuditRepository(AuditRepository):
    """
    The audit trail in the same database as everything else.

    Same file on purpose: an audit row and the expense it describes are then
    written by the same connection policy, backed up together, and cannot drift
    apart. A separate trail database is a trail that can go missing on its own.

    `source` names the surface this process is. It is set once, here, because
    the process is the thing that knows — the API and the terminal client run
    the same services, and a service asked to describe where it was running
    would be guessing.
    """

    def __init__(self, db_path, source="unknown"):
        self.source = source

        # Held for its connection handling, and for the side effect of running
        # migrations: the audit table has to exist before the first write, and
        # this is the one place that guarantees it has.
        self.storage = SqliteStorage(db_path)

    def record(self, event):
        event.source = self.source

        connection = self.storage.connection()

        try:
            cursor = connection.execute(
                """
                INSERT INTO audit_events
                    (happened_at, user_id, action, entity_type, entity_id, detail, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.happened_at,
                    event.user_id,
                    event.action,
                    event.entity_type,
                    event.entity_id,
                    event.detail_json(),
                    event.source,
                ),
            )
            connection.commit()

            event.id = cursor.lastrowid
        except sqlite3.Error as error:
            # Raised rather than swallowed, and not logged here: the caller is
            # the only layer that knows what a gap in the trail costs, and it
            # logs the consequence once. Logging in both places would put the
            # same traceback in the file twice.
            raise StorageError("Unable to write to the audit trail") from error
        finally:
            connection.close()

        return event

    def for_user(self, user_id, limit=100):
        connection = self.storage.connection()

        try:
            cursor = connection.execute(
                """
                SELECT id, happened_at, user_id, action, entity_type, entity_id, detail, source
                FROM audit_events
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            return [self._to_event(row) for row in cursor.fetchall()]
        except Exception as error:
            raise StorageError("Unable to read the audit trail") from error
        finally:
            connection.close()

    @staticmethod
    def _to_event(row):
        """A row back as an AuditEvent, in the order the SELECT above lists."""
        event_id, happened_at, user_id, action, entity_type, entity_id, detail, source = row

        return AuditEvent(
            action=action,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            detail=json.loads(detail) if detail is not None else None,
            source=source,
            happened_at=happened_at,
            id=event_id,
        )

def run(connection):
    """
    Creates the audit trail: one row per thing that happened, and who did it.

    Two deliberate choices, both of which would be easy to "fix" later by
    someone who did not know why they were made.

    **No foreign key to users or expenses.** expenses.user_id references
    users(id) and foreign keys are enforced (PRAGMA foreign_keys = ON), so a
    reference here would make deleting a user fail while their trail existed —
    and, worse, the moment anyone added ON DELETE CASCADE the record of the
    deletion would be deleted by the deletion. An audit row has to be able to
    outlive the thing it describes; that is the entire job. The cost is that
    user_id may name a row that no longer exists, which is correct here and
    would be a bug anywhere else in this schema.

    **AUTOINCREMENT rather than a bare INTEGER PRIMARY KEY.** SQLite reuses the
    largest rowid after a delete unless AUTOINCREMENT is declared. Ids that are
    never reused are what make the trail reassembleable without a timestamp
    tiebreak, and the cost is one extra table SQLite maintains. Nothing in this
    app deletes audit rows today; the point is that nothing has to be trusted
    not to.

    happened_at is UTC ISO-8601 with an explicit offset. Stored as text, which
    sorts correctly as text precisely because the offset is always the same and
    the format is fixed-width.
    """
    connection.execute(
        """
        CREATE TABLE audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            happened_at TEXT NOT NULL,
            user_id INTEGER,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            detail TEXT,
            source TEXT NOT NULL
        )
        """
    )

    # "What did this user do, most recently" — the question the trail is
    # actually opened to answer.
    connection.execute(
        """
        CREATE INDEX idx_audit_events_user
        ON audit_events (user_id, happened_at)
        """
    )

    # "What happened to this expense" — the other one.
    connection.execute(
        """
        CREATE INDEX idx_audit_events_entity
        ON audit_events (entity_type, entity_id)
        """
    )

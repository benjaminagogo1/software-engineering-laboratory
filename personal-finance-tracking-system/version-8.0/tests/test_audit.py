"""
The audit trail's contract, asserted against both implementations.

Every test in the upper half of this file runs twice — once against the
in-memory repository and once against the SQLite one — because the two are
supposed to be interchangeable behind AuditRepository, and the only way to know
they are is to hold both to the same assertions. A contract test written
against one of them is a test of that one.

The service-level question — *does* an expense deletion record an event — is
not here. It lives next to the code that answers it, in test_expense_service.py
and test_user_service.py.
"""

import pytest

from app.models.audit_event import AuditEvent, EXPENSE_CREATED, LOGIN_FAILED
from app.repositories.audit_repository import AuditRepository
from app.repositories.memory_audit_repository import MemoryAuditRepository
from app.repositories.sqlite_audit_repository import SqliteAuditRepository


@pytest.fixture(params=["memory", "sqlite"])
def audit(request, db_path):
    """
    Both stores, under one name.

    `source="test"` on both so the source assertions mean the same thing —
    MemoryAuditRepository's default is "memory", which would make the fixture
    the thing under test.
    """
    if request.param == "memory":
        return MemoryAuditRepository(source="test")

    return SqliteAuditRepository(db_path, source="test")


def event(action=EXPENSE_CREATED, user_id=1, detail=None, **kwargs):
    return AuditEvent(
        action=action,
        user_id=user_id,
        entity_type="expense",
        entity_id=7,
        detail=detail,
        **kwargs,
    )


def test_a_recorded_event_comes_back_with_an_id(audit):
    stored = audit.record(event())

    assert stored.id is not None


def test_ids_are_distinct_and_increasing(audit):
    """Two events must never be confusable by their id."""
    first = audit.record(event())
    second = audit.record(event())

    assert second.id > first.id


def test_the_store_stamps_its_own_source(audit):
    """
    Whatever the caller passes is overwritten. The source is where the process
    is running, and a caller is not in a position to know that.
    """
    stored = audit.record(event(source="somewhere-else"))

    assert stored.source == "test"


def test_the_timestamp_is_filled_in_by_default(audit):
    stored = audit.record(event())

    assert stored.happened_at


def test_an_explicit_timestamp_survives_the_round_trip(audit):
    """
    A backfilled event has to keep the time it happened rather than the time it
    was written, or the trail's ordering is a record of when rows were inserted.
    """
    stored = audit.record(event(happened_at="2020-01-02T03:04:05+00:00"))

    assert stored.happened_at == "2020-01-02T03:04:05+00:00"


def test_detail_round_trips_as_structured_data(audit):
    """detail is JSON in the column and a dict on the way out, nested included."""
    detail = {"amount": {"from": 1500.0, "to": 2000.0}, "tags": ["a", "b"], "note": None}

    stored = audit.record(event(detail=detail))

    assert stored.detail == detail


def test_an_event_without_detail_comes_back_without_detail(audit):
    """None, not the string "null" — the distinction survives storage."""
    stored = audit.record(event(detail=None))

    assert stored.detail is None


def test_every_field_comes_back_unchanged(audit):
    stored = audit.record(event(detail={"reason": "no such user"}, user_id=42))

    assert stored.action == EXPENSE_CREATED
    assert stored.user_id == 42
    assert stored.entity_type == "expense"
    assert stored.entity_id == 7


def test_for_user_returns_only_that_users_events(audit):
    audit.record(event(user_id=1))
    audit.record(event(user_id=2, action=LOGIN_FAILED))
    audit.record(event(user_id=1))

    assert [stored.user_id for stored in audit.for_user(1)] == [1, 1]


def test_for_user_returns_newest_first(audit):
    """The order the trail is read in: the most recent thing first."""
    audit.record(event(detail={"n": 1}))
    audit.record(event(detail={"n": 2}))
    audit.record(event(detail={"n": 3}))

    assert [stored.detail["n"] for stored in audit.for_user(1)] == [3, 2, 1]


def test_for_user_honours_the_limit(audit):
    for number in range(5):
        audit.record(event(detail={"n": number}))

    assert [stored.detail["n"] for stored in audit.for_user(1, limit=2)] == [4, 3]


def test_for_user_is_empty_when_nothing_was_recorded(audit):
    assert audit.for_user(1) == []


def test_an_event_with_no_user_is_not_attributed_to_anyone(audit):
    """
    A failed login against a username that does not exist has no user to
    attribute it to, and inventing one would put an attempt on a stranger's
    trail.
    """
    audit.record(event(action=LOGIN_FAILED, user_id=None))

    assert audit.for_user(1) == []


def test_a_trail_survives_a_second_repository_over_the_same_database(db_path):
    """
    The SQLite-specific property, stated directly rather than through the
    fixture: the trail is on disk, so a new process reads what the last one
    wrote. This is the difference the SQLite repository exists to provide.
    """
    SqliteAuditRepository(db_path, source="api").record(event(detail={"n": 1}))

    reopened = SqliteAuditRepository(db_path, source="cli")

    assert [stored.detail["n"] for stored in reopened.for_user(1)] == [1]


def test_the_interface_offers_no_way_to_change_or_remove_an_event():
    """
    The absence is the feature, so it gets a test.

    If update or delete ever appears on AuditRepository, this fails and the
    person adding it has to argue for it here — which is the point. A trail
    with an edit method is a trail that can be made to agree with whatever
    story is convenient.
    """
    forbidden = {"update", "delete", "remove", "clear", "delete_all", "edit"}

    public = {
        name
        for name in dir(AuditRepository)
        if not name.startswith("_")
    }

    assert public & forbidden == set()


def test_an_incomplete_repository_cannot_be_constructed():
    """AuditRepository is an abstract base, not a set of conventions."""

    class Half(AuditRepository):
        def record(self, audit_event):
            return audit_event

    with pytest.raises(TypeError):
        Half()


def test_a_failing_write_is_reported_as_a_storage_error(tmp_path):
    """
    The repository raises rather than logging, because it is the caller — the
    service — that knows what a gap in the trail costs. It also has to raise
    something specific: a bare sqlite3.Error leaking out of the storage layer
    would be the one place in this codebase where that happened.
    """
    from app.storage.storage_error import StorageError

    audit = SqliteAuditRepository(tmp_path / "broken.db", source="test")

    # Dropped out from under it, the way a corrupted file would look from here.
    connection = audit.storage.connection()

    try:
        connection.execute("DROP TABLE audit_events")
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(StorageError):
        audit.record(event())

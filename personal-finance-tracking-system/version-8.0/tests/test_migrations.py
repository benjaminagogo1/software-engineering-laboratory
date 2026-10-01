import importlib
import sqlite3
from datetime import date

import pytest

import app.storage.migration_runner as migration_runner
from app.storage.migration_runner import run_migrations


ALL_MIGRATIONS = list(migration_runner.migration_files)


def migrations_up_to(number):
    return [
        migration_file
        for migration_file in ALL_MIGRATIONS
        if int(migration_file.stem.split("_")[0]) <= number
    ]


def test_the_suite_covers_every_migration():
    """Guards against a migration file that never gets exercised here."""
    assert [int(f.stem.split("_")[0]) for f in ALL_MIGRATIONS] == [0, 1, 2, 3, 4, 5, 6, 7]


def test_date_migration_preserves_existing_expenses(tmp_path, monkeypatch):
    """
    The date column is added by rebuilding the expenses table, which is the
    one migration that could lose data if it were written wrong.
    """
    connection = sqlite3.connect(tmp_path / "legacy.db")

    # Build the schema exactly as it was before dates were tracked.
    monkeypatch.setattr(migration_runner, "migration_files", migrations_up_to(3))
    run_migrations(connection)

    connection.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("benjamin", "test-password-hash")
    )
    connection.execute(
        "INSERT INTO expenses (id, name, amount, user_id) VALUES (?, ?, ?, ?)",
        (7, "Transport", 1500.0, 1)
    )
    connection.commit()

    monkeypatch.setattr(migration_runner, "migration_files", ALL_MIGRATIONS)
    run_migrations(connection)

    row = connection.execute(
        "SELECT id, name, amount, user_id, date FROM expenses"
    ).fetchone()

    assert row == (7, "Transport", 1500.0, 1, date.today().isoformat())

    connection.close()


def test_category_and_payment_type_are_backfilled(tmp_path, monkeypatch):
    """
    Expenses that predate the two new fields must end up filed as "Other"
    rather than null, since both columns are NOT NULL.
    """
    connection = sqlite3.connect(tmp_path / "legacy.db")

    monkeypatch.setattr(migration_runner, "migration_files", migrations_up_to(4))
    run_migrations(connection)

    connection.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("benjamin", "test-password-hash")
    )
    connection.execute(
        """
        INSERT INTO expenses (id, name, amount, user_id, date)
        VALUES (?, ?, ?, ?, ?)
        """,
        (7, "Transport", 1500.0, 1, "2026-03-02")
    )
    connection.commit()

    monkeypatch.setattr(migration_runner, "migration_files", ALL_MIGRATIONS)
    run_migrations(connection)

    row = connection.execute(
        "SELECT id, name, amount, date, category, payment_type FROM expenses"
    ).fetchone()

    assert row == (7, "Transport", 1500.0, "2026-03-02", "Other", "Other")

    connection.close()


def test_the_index_survives_the_category_migration(tmp_path, monkeypatch):
    """
    Migration 005 rebuilds the table, and dropping a table drops its indexes
    with it — so it has to recreate the one migration 004 added.
    """
    connection = sqlite3.connect(tmp_path / "legacy.db")
    monkeypatch.setattr(migration_runner, "migration_files", ALL_MIGRATIONS)
    run_migrations(connection)

    indexes = [
        row[1] for row in connection.execute(
            "SELECT type, name FROM sqlite_master WHERE type = 'index'"
        )
    ]

    assert "idx_expenses_user_date" in indexes

    connection.close()


def test_expenses_without_an_owner_still_migrate(tmp_path, monkeypatch):
    """Rows predating user ownership have a NULL user_id and must survive too."""
    connection = sqlite3.connect(tmp_path / "legacy.db")

    monkeypatch.setattr(migration_runner, "migration_files", migrations_up_to(3))
    run_migrations(connection)

    connection.execute(
        "INSERT INTO expenses (id, name, amount, user_id) VALUES (?, ?, ?, ?)",
        (1, "Food", 1000.0, None)
    )
    connection.commit()

    monkeypatch.setattr(migration_runner, "migration_files", ALL_MIGRATIONS)
    run_migrations(connection)

    row = connection.execute("SELECT name, user_id, date FROM expenses").fetchone()

    assert row == ("Food", None, date.today().isoformat())

    connection.close()


def test_the_new_columns_are_not_null(tmp_path, monkeypatch):
    connection = sqlite3.connect(tmp_path / "legacy.db")
    monkeypatch.setattr(migration_runner, "migration_files", ALL_MIGRATIONS)
    run_migrations(connection)

    columns = {
        row[1]: row for row in connection.execute("PRAGMA table_info(expenses)")
    }

    assert columns["date"][3] == 1
    assert columns["category"][3] == 1
    assert columns["payment_type"][3] == 1

    connection.close()


def test_migrations_are_idempotent(tmp_path, monkeypatch):
    connection = sqlite3.connect(tmp_path / "legacy.db")
    monkeypatch.setattr(migration_runner, "migration_files", ALL_MIGRATIONS)

    run_migrations(connection)
    run_migrations(connection)

    applied = connection.execute("SELECT COUNT(*) FROM migrations").fetchone()[0]

    assert applied == len(ALL_MIGRATIONS)

    connection.close()


def test_the_migration_directory_is_absolute():
    """
    A relative path is resolved against the working directory, so the runner
    found the migrations only when the process happened to be started from the
    project root.
    """
    assert migration_runner.MIGRATION_DIR.is_absolute()


def test_the_migration_directory_is_the_packages_own():
    """
    Not merely an absolute path: the one next to this module. An absolute
    `/migrations` would be found, be wrong, and fail only in production.
    """
    assert migration_runner.MIGRATION_DIR.name == "migrations"
    assert (migration_runner.MIGRATION_DIR.parent / "migration_runner.py").is_file()


def test_discovery_does_not_depend_on_the_working_directory(tmp_path, monkeypatch):
    """
    The regression, reproduced the way it was actually reached: start the app
    from somewhere other than the project root.

    Reloading is the point. The module-level `migration_files` is computed once,
    at import, so a test that merely changed directory afterwards would still
    see the list built earlier and pass against the broken code.
    """
    monkeypatch.chdir(tmp_path)

    reloaded = importlib.reload(migration_runner)

    assert [file.name for file in reloaded.migration_files] == [
        file.name for file in ALL_MIGRATIONS
    ]


def test_a_missing_directory_is_an_error_rather_than_an_empty_list(tmp_path):
    """
    The reason the bug was invisible: `glob` on a path that does not exist
    returns nothing, so the runner iterated an empty list, recorded no
    migrations and reported success — leaving a database with no schema and
    nothing to say so.
    """
    with pytest.raises(RuntimeError, match="Migration directory not found"):
        migration_runner.discover_migrations(tmp_path / "nowhere")


def test_an_empty_directory_is_an_error_too(tmp_path):
    empty = tmp_path / "migrations"
    empty.mkdir()

    with pytest.raises(RuntimeError, match="No migrations found"):
        migration_runner.discover_migrations(empty)


def test_discovery_returns_the_files_in_order(tmp_path):
    directory = tmp_path / "migrations"
    directory.mkdir()

    # Deliberately created out of order, so a sorted result is the assertion
    # and not an accident of directory listing order.
    for name in ("002_second.py", "000_first.py", "001_middle.py"):
        (directory / name).write_text("def run(connection):\n    pass\n")

    found = migration_runner.discover_migrations(directory)

    assert [file.name for file in found] == [
        "000_first.py",
        "001_middle.py",
        "002_second.py",
    ]


def test_merchant_and_note_migration_preserves_existing_expenses(tmp_path, monkeypatch):
    """
    006 adds two nullable columns with ALTER TABLE — no table rebuild — so
    existing rows must come through untouched, with nothing recorded for
    either new field.
    """
    connection = sqlite3.connect(tmp_path / "legacy.db")

    monkeypatch.setattr(migration_runner, "migration_files", migrations_up_to(5))
    run_migrations(connection)

    connection.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("benjamin", "test-password-hash")
    )
    connection.execute(
        """
        INSERT INTO expenses (id, name, amount, user_id, date, category, payment_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (7, "Transport", 1500.0, 1, "2026-03-02", "Transport", "Cash")
    )
    connection.commit()

    monkeypatch.setattr(migration_runner, "migration_files", ALL_MIGRATIONS)
    run_migrations(connection)

    row = connection.execute(
        """
        SELECT id, name, amount, user_id, date, category, payment_type, merchant, note
        FROM expenses
        """
    ).fetchone()

    assert row == (
        7, "Transport", 1500.0, 1, "2026-03-02", "Transport", "Cash", None, None
    )

    connection.close()


def test_the_merchant_and_note_columns_are_nullable(tmp_path, monkeypatch):
    """
    Unlike date, category and payment_type, these two are optional — PRAGMA's
    notnull flag has to be 0, or an expense with no payee could not be stored
    at all.
    """
    connection = sqlite3.connect(tmp_path / "legacy.db")
    monkeypatch.setattr(migration_runner, "migration_files", ALL_MIGRATIONS)
    run_migrations(connection)

    columns = {
        row[1]: row for row in connection.execute("PRAGMA table_info(expenses)")
    }

    assert columns["merchant"][3] == 0
    assert columns["note"][3] == 0

    connection.close()


def test_the_audit_table_requires_a_time_an_action_and_a_source(tmp_path, monkeypatch):
    """
    A row that cannot say what happened, when, or from where is not an audit
    row. user_id, entity_type, entity_id and detail are all legitimately
    absent for some events — a failed login against an unknown username has no
    user — so those stay nullable.
    """
    connection = sqlite3.connect(tmp_path / "legacy.db")
    monkeypatch.setattr(migration_runner, "migration_files", ALL_MIGRATIONS)
    run_migrations(connection)

    columns = {
        row[1]: row for row in connection.execute("PRAGMA table_info(audit_events)")
    }

    assert columns["happened_at"][3] == 1
    assert columns["action"][3] == 1
    assert columns["source"][3] == 1

    assert columns["user_id"][3] == 0
    assert columns["entity_id"][3] == 0
    assert columns["detail"][3] == 0

    connection.close()


def test_the_audit_table_has_no_foreign_keys(tmp_path, monkeypatch):
    """
    The deliberate omission, pinned so it is not "corrected" later.

    A foreign key to users would make an audit row block the deletion of the
    user it describes, and adding ON DELETE CASCADE — the obvious fix once
    someone hits that — would delete the record of the deletion, by the
    deletion. An audit row has to be able to outlive its subject.
    """
    connection = sqlite3.connect(tmp_path / "legacy.db")
    monkeypatch.setattr(migration_runner, "migration_files", ALL_MIGRATIONS)
    run_migrations(connection)

    references = connection.execute("PRAGMA foreign_key_list(audit_events)").fetchall()

    assert references == []

    connection.close()


def test_audit_ids_are_never_reused(tmp_path, monkeypatch):
    """
    Why the column is AUTOINCREMENT and not a bare INTEGER PRIMARY KEY.

    Without it SQLite hands the rowid of a deleted row to the next insert, so
    an id that has already been written down elsewhere would silently come to
    mean a different event.
    """
    connection = sqlite3.connect(tmp_path / "legacy.db")
    monkeypatch.setattr(migration_runner, "migration_files", ALL_MIGRATIONS)
    run_migrations(connection)

    insert = """
        INSERT INTO audit_events (happened_at, action, source)
        VALUES ('2026-09-30T00:00:00+00:00', ?, 'test')
    """

    connection.execute(insert, ("expense.created",))
    first_id = connection.execute("SELECT MAX(id) FROM audit_events").fetchone()[0]

    connection.execute("DELETE FROM audit_events WHERE id = ?", (first_id,))

    connection.execute(insert, ("expense.deleted",))
    second_id = connection.execute("SELECT MAX(id) FROM audit_events").fetchone()[0]

    assert second_id > first_id

    connection.close()


def test_the_audit_table_is_indexed_by_user_and_by_entity(tmp_path, monkeypatch):
    """
    The trail is only ever read by one of two questions — what did this user
    do, and what happened to this expense — and both have to stay cheap as the
    table grows, which it only ever does.
    """
    connection = sqlite3.connect(tmp_path / "legacy.db")
    monkeypatch.setattr(migration_runner, "migration_files", ALL_MIGRATIONS)
    run_migrations(connection)

    indexes = [
        row[1] for row in connection.execute(
            "SELECT type, name FROM sqlite_master WHERE type = 'index'"
        )
    ]

    assert "idx_audit_events_user" in indexes
    assert "idx_audit_events_entity" in indexes

    connection.close()


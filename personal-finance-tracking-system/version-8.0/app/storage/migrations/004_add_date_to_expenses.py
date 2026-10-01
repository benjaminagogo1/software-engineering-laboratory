def run(connection):
    """
    Adds the date column the analytics features group by.

    SQLite refuses a non-constant DEFAULT on ALTER TABLE ADD COLUMN, so a plain
    ADD COLUMN could only make date nullable. Rebuilding the table instead — the
    same pattern migration 003 uses — lets date be NOT NULL, and backfills the
    rows that existed before dates were tracked.

    expenses is the child side of the users foreign key (never a parent), so
    dropping it is safe with PRAGMA foreign_keys = ON.
    """
    connection.execute(
        """
        CREATE TABLE expenses_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            user_id INTEGER,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    connection.execute(
        """
        INSERT INTO expenses_new (id, name, amount, user_id, date)
        SELECT id, name, amount, user_id, date('now')
        FROM expenses
        """
    )

    connection.execute("DROP TABLE expenses")

    connection.execute(
        "ALTER TABLE expenses_new RENAME TO expenses"
    )

    # Feature 1 groups by month within a user, so both columns lead the index.
    connection.execute(
        """
        CREATE INDEX idx_expenses_user_date
        ON expenses (user_id, date)
        """
    )

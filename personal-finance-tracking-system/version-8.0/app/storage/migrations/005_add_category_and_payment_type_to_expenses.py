def run(connection):
    """
    Adds the category and payment_type columns.

    Another table rebuild: SQLite cannot ADD COLUMN with NOT NULL and no
    default, and these two are required. Rows that predate them are filed as
    "Other" so no expense ends up with a null category.

    The literals are hardcoded rather than imported from app.models.expense on
    purpose — a migration is a snapshot of the schema at one point in time and
    must not change meaning if those constants are edited later.

    Dropping the table also drops its indexes, so migration 004's index is
    recreated at the end.
    """
    connection.execute(
        """
        CREATE TABLE expenses_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            user_id INTEGER,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            payment_type TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    connection.execute(
        """
        INSERT INTO expenses_new
            (id, name, amount, user_id, date, category, payment_type)
        SELECT id, name, amount, user_id, date, 'Other', 'Other'
        FROM expenses
        """
    )

    connection.execute("DROP TABLE expenses")

    connection.execute(
        "ALTER TABLE expenses_new RENAME TO expenses"
    )

    connection.execute(
        """
        CREATE INDEX idx_expenses_user_date
        ON expenses (user_id, date)
        """
    )

def run(connection):
    """
    Converts amount from REAL naira to INTEGER kobo, and adds the constraints
    the column never had.

    A rebuild rather than an ALTER, because SQLite cannot change a column's
    declared type, and because the CHECK constraints have to be part of the
    table definition. Same shape as 005: create, copy, drop, rename, recreate
    the index.

    The literals for category and payment_type are hardcoded rather than
    imported from app.models.expense, for the same reason 005 hardcoded them —
    a migration is a snapshot of the schema at one point in time and must not
    change meaning if those constants are edited later.

    `typeof(amount_cents) = 'integer'` is not redundant with the column type.
    SQLite columns have type *affinity*, not a type: a REAL that cannot be
    represented as an integer is stored as REAL even in an INTEGER column, so
    `CHECK (amount_cents > 0)` alone would happily accept 2500.5. This is the
    constraint that actually makes "money is a whole number of kobo" true of
    the file itself rather than only of the code that writes it.

    A row that cannot satisfy the constraints aborts the migration, and because
    the runner wraps each one in a transaction the database is left exactly as
    it was. That is deliberate: an amount of 0, or a category this schema does
    not know, is a fact about the data that needs a decision, not something to
    coerce quietly on the way past.
    """
    connection.execute(
        """
        CREATE TABLE expenses_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount_cents INTEGER NOT NULL
                CHECK (amount_cents > 0 AND typeof(amount_cents) = 'integer'),
            user_id INTEGER,
            date TEXT NOT NULL,
            category TEXT NOT NULL
                CHECK (category IN ('Food', 'Transport', 'Bills', 'Rent',
                                    'Health', 'Entertainment', 'Other')),
            payment_type TEXT NOT NULL
                CHECK (payment_type IN ('Cash', 'Card', 'Transfer',
                                        'Mobile Money', 'Other')),
            merchant TEXT,
            note TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    # ROUND before the cast: ROUND returns a float, and the cast truncates, so
    # casting 2499.9999999999995 without rounding first would lose a kobo.
    # Existing rows are all whole naira, so nothing here should round at all —
    # this is for the database that has a stray 2500.005 in it.
    connection.execute(
        """
        INSERT INTO expenses_new
            (id, name, amount_cents, user_id, date, category, payment_type,
             merchant, note)
        SELECT id, name, CAST(ROUND(amount * 100) AS INTEGER), user_id, date,
               category, payment_type, merchant, note
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

    # Nothing references expenses today, so this should always be empty — which
    # is exactly why it is worth asserting rather than assuming. If a later
    # migration adds a table that does, the rebuild above stops being safe and
    # this is where that surfaces, while the transaction can still undo it.
    violations = connection.execute("PRAGMA foreign_key_check").fetchall()

    if violations:
        raise RuntimeError(
            f"Migration 008 left {len(violations)} foreign key violation(s); "
            "refusing to commit the rebuilt expenses table."
        )

def run(connection):
    """
    Adds the optional merchant and note columns.

    Unlike migrations 004 and 005 this needs no table rebuild: both columns are
    nullable, and SQLite is happy to ADD COLUMN with an implicit NULL default.
    That matters beyond brevity — a rebuild means DROP TABLE, which would drop
    idx_expenses_user_date again along with every row's identity.

    Existing expenses get NULL for both, which is the honest answer: nobody
    recorded a payee for them.
    """
    connection.execute(
        "ALTER TABLE expenses ADD COLUMN merchant TEXT"
    )

    connection.execute(
        "ALTER TABLE expenses ADD COLUMN note TEXT"
    )

def run(connection):
    connection.execute(
        """
        CREATE TABLE expenses_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    connection.execute(
        """
        INSERT INTO expenses_new (id, name, amount, user_id)
        SELECT id, name, amount, user_id
        FROM expenses
        """
    )

    connection.execute("DROP TABLE expenses")

    connection.execute(
        "ALTER TABLE expenses_new RENAME TO expenses"
    )
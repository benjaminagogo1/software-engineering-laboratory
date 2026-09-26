


def run(connection):
      connection.execute(
            """
            CREATE IF NOT EXISTS expenses (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  amount REAL NOT NUL
            )
            """
      )
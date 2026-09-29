


def run(connection):
      connection.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  amount REAL NOT NULL
            )
            """
      )
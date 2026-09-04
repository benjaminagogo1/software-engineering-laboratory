import sqlite3
from app.storage.storage_error import StorageError


class SqliteStorage:
    """
    Owns the raw connection to the SQLite database and knows nothing
    about Expense objects. It only speaks in rows and SQL — same
    responsibility JsonStorage had for JSON, just a different format.
    """

    def __init__(self, db_path):
        self.db_path = db_path
        self._create_table_if_missing()

    def _connect(self):
        try:
            return sqlite3.connect(self.db_path)
        except sqlite3.Error as error:
            raise StorageError("Unable to connect to the expense database") from error

    def _create_table_if_missing(self):
        connection = self._connect()

        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS expenses (
                    id     INTEGER PRIMARY KEY AUTOINCREMENT,
                    name   TEXT NOT NULL,
                    amount REAL NOT NULL
                )
                """
            )
            connection.commit()
        except sqlite3.Error as error:
            raise StorageError("Unable to set up the expense database") from error
        finally:
            connection.close()

    def fetch_all(self):
        connection = self._connect()

        try:
            cursor = connection.execute("SELECT id, name, amount FROM expenses")
            return cursor.fetchall()
        except sqlite3.Error as error:
            raise StorageError("Unable to read expenses from the database") from error
        finally:
            connection.close()

    def fetch_by_id(self, expense_id):
        connection = self._connect()

        try:
            cursor = connection.execute(
                "SELECT id, name, amount FROM expenses WHERE id = ?",
                (expense_id,),
            )
            return cursor.fetchone()
        except sqlite3.Error as error:
            raise StorageError("Unable to read the expense from the database") from error
        finally:
            connection.close()

    def insert(self, name, amount):
        connection = self._connect()

        try:
            cursor = connection.execute(
                "INSERT INTO expenses (name, amount) VALUES (?, ?)",
                (name, amount),
            )
            connection.commit()
            return cursor.lastrowid
        except sqlite3.Error as error:
            raise StorageError("Unable to save the expense to the database") from error
        finally:
            connection.close()

    def update(self, expense_id, name, amount):
        connection = self._connect()

        try:
            connection.execute(
                "UPDATE expenses SET name = ?, amount = ? WHERE id = ?",
                (name, amount, expense_id),
            )
            connection.commit()
        except sqlite3.Error as error:
            raise StorageError("Unable to update the expense in the database") from error
        finally:
            connection.close()

    def delete(self, expense_id):
        connection = self._connect()

        try:
            connection.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            connection.commit()
        except sqlite3.Error as error:
            raise StorageError("Unable to delete the expense from the database") from error
        finally:
            connection.close()

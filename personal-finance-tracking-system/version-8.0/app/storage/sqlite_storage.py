import sqlite3
from app.storage.migration_runner import run_migrations
from app.storage.storage_error import StorageError
import logging



logger = logging.getLogger(__name__)

class SqliteStorage:
    """
    Owns the raw connection to the SQLite database and knows nothing
    about Expense objects. It only speaks in rows and SQL — same
    responsibility JsonStorage had for JSON, just a different format.
    """

    def __init__(self, db_path):
        self.db_path = db_path

        connection =  self._connect()

        try:
            run_migrations(connection)
        finally:
            connection.close()

    def _connect(self): 
        try:
            connection = sqlite3.connect(self.db_path)
            connection.execute("PRAGMA foreign_keys = ON")
            return connection
        except sqlite3.Error as error:
            logger.exception("Unable to connect to the expense database")
            raise StorageError(
                "Unable to connect to the expense database"
                ) from error

    # def _create_table_if_missing(self):
    #     connection = self._connect()

    #     try:
    #         connection.execute(
    #             """
    #             CREATE TABLE IF NOT EXISTS expenses (
    #                 id     INTEGER PRIMARY KEY AUTOINCREMENT,
    #                 name   TEXT NOT NULL,
    #                 amount REAL NOT NULL
    #             )
    #             """
    #         )
    #         connection.commit()
    #     except sqlite3.Error as error:
    #         raise StorageError("Unable to set up the expense database") from error
    #     finally:
    #         connection.close()

    def fetch_all(self, user_id):
        connection = self._connect()

        try:
            cursor = connection.execute(
                "SELECT id, name, amount, user_id FROM expenses WHERE user_id = ?",
                (user_id,))
            return cursor.fetchall()
        except sqlite3.Error as error:
            raise StorageError("Unable to read expenses from the database") from error
        finally:
            connection.close()

    def fetch_by_id(self, expense_id, user_id):
        connection = self._connect()

        try:
            cursor = connection.execute(
                """
                SELECT id, name, amount, user_id 
                FROM expenses WHERE id = ? AND user_id = ?
                """,
                (expense_id, user_id),
            )
            return cursor.fetchone()
        
        except sqlite3.Error as error:
            raise StorageError("Unable to read the expense from the database") from error
        finally:
            connection.close()

    def insert(self, name, amount, user_id):
        connection = self._connect()

        try:
            cursor = connection.execute(
                "INSERT INTO expenses (name, amount, user_id) VALUES (?, ?, ?)",
                (name, amount, user_id),
            )
            connection.commit()
            return cursor.lastrowid
        except sqlite3.Error as error:
            logger.exception("Unable to save expense")
            raise StorageError(
                "Unable to save the expense to the database"
            ) from error
        finally:
            connection.close()


    def insert_user(self, username, password_hash):
        connection = self._connect()

        try:
            cursor = connection.execute(
                """
                INSERT INTO users (username, password_hash)
                VALUES (?, ?)
                """,
                (username, password_hash),
            )
            connection.commit()
            return cursor.lastrowid
        except sqlite3.Error as error:
            logger.exception("Unable to save user")
            raise StorageError(
                "Unable to save the user to the database"
            ) from error
        finally:
            connection.close()


    def fetch_user_by_username(self, username):
        with self._connect() as connection:
            cursor = connection.execute(
                """
                SELECT id, username, password_hash
                FROM users
                WHERE username = ?
                """,
                (username,)
        )
        return cursor.fetchone()

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

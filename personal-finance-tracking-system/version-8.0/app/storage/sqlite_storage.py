import sqlite3
from app.storage.migration_runner import run_migrations
from app.storage.storage_error import StorageError
import logging



logger = logging.getLogger(__name__)


# Every SELECT lists its columns explicitly, in this order, because the
# repository maps rows back positionally. Appending a column here means
# appending it in SqliteExpenseRepository._to_expense too.
EXPENSE_COLUMNS = (
    "id, name, amount_cents, user_id, date, category, payment_type, merchant, note"
)


def _escape_like(term):
    """
    Escapes LIKE wildcards so a search for "%" looks for a literal percent
    sign instead of matching every row.

    The backslash must be escaped first, otherwise it would double-escape the
    backslashes introduced by the two replacements after it.
    """
    return (
        term.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


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

    def connection(self):
        """
        A new connection to this database, with its pragmas already applied.
        The caller is responsible for closing it.

        Public because the audit repository stores something other than
        expenses and still has to connect the same way. It reuses this rather
        than opening its own sqlite3 connection so that "how we connect" has
        exactly one definition — two would eventually disagree about foreign
        keys, and the disagreement would only show up under load.
        """
        return self._connect()

    def fetch_all(self, user_id):
        connection = self._connect()

        try:
            cursor = connection.execute(
                f"""
                SELECT {EXPENSE_COLUMNS}
                FROM expenses WHERE user_id = ?
                ORDER BY id
                """,
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
                f"""
                SELECT {EXPENSE_COLUMNS}
                FROM expenses WHERE id = ? AND user_id = ?
                """,
                (expense_id, user_id),
            )
            return cursor.fetchone()

        except sqlite3.Error as error:
            raise StorageError("Unable to read the expense from the database") from error
        finally:
            connection.close()

    def fetch_highest(self, user_id):
        """
        The single most expensive expense. Ordering by id as well keeps the
        result stable when two expenses share the same amount.
        """
        connection = self._connect()

        try:
            cursor = connection.execute(
                f"""
                SELECT {EXPENSE_COLUMNS}
                FROM expenses WHERE user_id = ?
                ORDER BY amount_cents DESC, id ASC
                LIMIT 1
                """,
                (user_id,),
            )
            return cursor.fetchone()
        except sqlite3.Error as error:
            raise StorageError("Unable to read expenses from the database") from error
        finally:
            connection.close()

    def fetch_lowest(self, user_id):
        """
        The single cheapest expense — the exact mirror of fetch_highest, so an
        amount tie resolves the same way, to the lower id.
        """
        connection = self._connect()

        try:
            cursor = connection.execute(
                f"""
                SELECT {EXPENSE_COLUMNS}
                FROM expenses WHERE user_id = ?
                ORDER BY amount_cents ASC, id ASC
                LIMIT 1
                """,
                (user_id,),
            )
            return cursor.fetchone()
        except sqlite3.Error as error:
            raise StorageError("Unable to read expenses from the database") from error
        finally:
            connection.close()

    def fetch_top_month(self, user_id):
        """
        The month with the highest total spending, as (month, total) where
        month is "YYYY-MM". Equal totals resolve to the most recent month.
        """
        connection = self._connect()

        try:
            cursor = connection.execute(
                """
                SELECT strftime('%Y-%m', date) AS month, SUM(amount_cents) AS total
                FROM expenses WHERE user_id = ?
                GROUP BY month
                ORDER BY total DESC, month DESC
                LIMIT 1
                """,
                (user_id,),
            )
            return cursor.fetchone()
        except sqlite3.Error as error:
            raise StorageError("Unable to read expenses from the database") from error
        finally:
            connection.close()

    def fetch_month_totals(self, user_id):
        """
        Every month's total, most expensive first — the whole ranking rather
        than just its winner. The ORDER BY is identical to fetch_top_month's
        minus the LIMIT, so this list's first row is always what that returns.
        """
        connection = self._connect()

        try:
            cursor = connection.execute(
                """
                SELECT strftime('%Y-%m', date) AS month, SUM(amount_cents) AS total
                FROM expenses WHERE user_id = ?
                GROUP BY month
                ORDER BY total DESC, month DESC
                """,
                (user_id,),
            )
            return cursor.fetchall()
        except sqlite3.Error as error:
            raise StorageError("Unable to read expenses from the database") from error
        finally:
            connection.close()

    def fetch_top_weekday(self, user_id):
        """
        The weekday with the highest total spending, as (weekday_number, total)
        with Sunday as 0 — the numbering strftime('%w') already uses.

        Deliberately not naming the days here: this layer speaks rows, and the
        name is applied on the way out so both repositories agree on it.
        """
        connection = self._connect()

        try:
            cursor = connection.execute(
                """
                SELECT strftime('%w', date) AS weekday, SUM(amount_cents) AS total
                FROM expenses WHERE user_id = ?
                GROUP BY weekday
                ORDER BY total DESC, weekday ASC
                LIMIT 1
                """,
                (user_id,),
            )
            return cursor.fetchone()
        except sqlite3.Error as error:
            raise StorageError("Unable to read expenses from the database") from error
        finally:
            connection.close()

    def fetch_daily_totals(self, month, user_id):
        """
        Per-day totals within one month ("YYYY-MM"), as (date, total) rows.

        Only days that actually have spending come back — padding the month out
        to 31 rows is a presentation decision, and it needs the calendar, which
        this layer has no business knowing about.
        """
        connection = self._connect()

        try:
            cursor = connection.execute(
                """
                SELECT date, SUM(amount_cents) AS total
                FROM expenses
                WHERE user_id = ? AND strftime('%Y-%m', date) = ?
                GROUP BY date
                ORDER BY date
                """,
                (user_id, month),
            )
            return cursor.fetchall()
        except sqlite3.Error as error:
            raise StorageError("Unable to read expenses from the database") from error
        finally:
            connection.close()

    def count_by_name(self, name, user_id):
        """
        How many times an expense name appears. COLLATE NOCASE makes the
        comparison case-insensitive — unlike LIKE, an equality test does
        honour a collation.
        """
        connection = self._connect()

        try:
            cursor = connection.execute(
                """
                SELECT COUNT(*) FROM expenses
                WHERE user_id = ? AND name = ? COLLATE NOCASE
                """,
                (user_id, name),
            )
            return cursor.fetchone()[0]
        except sqlite3.Error as error:
            raise StorageError("Unable to read expenses from the database") from error
        finally:
            connection.close()

    def search_by_name(self, name, user_id):
        """
        Expenses whose name contains the search term. LIKE is already
        case-insensitive for ASCII in SQLite, hence no COLLATE NOCASE here.
        """
        connection = self._connect()

        try:
            cursor = connection.execute(
                f"""
                SELECT {EXPENSE_COLUMNS}
                FROM expenses
                WHERE user_id = ? AND name LIKE ? ESCAPE '\\'
                ORDER BY id
                """,
                (user_id, f"%{_escape_like(name)}%"),
            )
            return cursor.fetchall()
        except sqlite3.Error as error:
            raise StorageError("Unable to read expenses from the database") from error
        finally:
            connection.close()

    def insert(
        self,
        name,
        amount_cents,
        date,
        category,
        payment_type,
        merchant,
        note,
        user_id,
    ):
        connection = self._connect()

        try:
            cursor = connection.execute(
                """
                INSERT INTO expenses
                    (name, amount_cents, date, category, payment_type, merchant, note, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (name, amount_cents, date, category, payment_type, merchant, note, user_id),
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
        connection = self._connect()

        try:
            cursor = connection.execute(
                """
                SELECT id, username, password_hash
                FROM users
                WHERE username = ?
                """,
                (username,)
            )
            return cursor.fetchone()
        except sqlite3.Error as error:
            raise StorageError("Unable to read the user from the database") from error
        finally:
            # A sqlite3 connection used as a context manager commits on exit but
            # never closes, so this must be explicit or every login leaks a
            # connection.
            connection.close()

    def fetch_user_by_id(self, user_id):
        connection = self._connect()

        try:
            cursor = connection.execute(
                """
                SELECT id, username, password_hash
                FROM users
                WHERE id = ?
                """,
                (user_id,)
            )
            return cursor.fetchone()
        except sqlite3.Error as error:
            raise StorageError("Unable to read the user from the database") from error
        finally:
            connection.close()

    def update(
        self,
        expense_id,
        name,
        amount_cents,
        date,
        category,
        payment_type,
        merchant,
        note,
        user_id,
    ):
        connection = self._connect()

        try:
            connection.execute(
                """
                UPDATE expenses
                SET name = ?, amount_cents = ?, date = ?, category = ?,
                    payment_type = ?, merchant = ?, note = ?
                WHERE id = ? AND user_id = ?
                """,
                (
                    name,
                    amount_cents,
                    date,
                    category,
                    payment_type,
                    merchant,
                    note,
                    expense_id,
                    user_id,
                ),
            )
            connection.commit()
        except sqlite3.Error as error:
            raise StorageError("Unable to update the expense in the database") from error
        finally:
            connection.close()

    def delete(self, expense_id, user_id):
        connection = self._connect()

        try:
            connection.execute(
                "DELETE FROM expenses WHERE id = ? AND user_id = ?",
                (expense_id, user_id),
            )
            connection.commit()
        except sqlite3.Error as error:
            raise StorageError("Unable to delete the expense from the database") from error
        finally:
            connection.close()

    def delete_all(self, user_id):
        """
        Removes every expense belonging to one user and reports how many went.

        The WHERE clause is the whole safety story here: this is the only
        statement in the class that can destroy many rows at once, and it must
        never be able to reach another user's.
        """
        connection = self._connect()

        try:
            cursor = connection.execute(
                "DELETE FROM expenses WHERE user_id = ?",
                (user_id,),
            )
            connection.commit()
            return cursor.rowcount
        except sqlite3.Error as error:
            raise StorageError("Unable to delete the expenses from the database") from error
        finally:
            connection.close()

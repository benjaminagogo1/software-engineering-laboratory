from app.repositories.expense_repository import ExpenseRepository
from app.models.expense import Expense, weekday_name
from app.storage.sqlite_storage import SqliteStorage


class SqliteExpenseRepository(ExpenseRepository):
    """
    Same contract as JsonExpenseRepository — add / get_all / find_by_id /
    update / delete — just backed by SQLite instead of a JSON file.

    Because ExpenseService only depends on the ExpenseRepository interface,
    it doesn't need to change at all to work with this class. That's the
    payoff of the abstraction introduced back in v4.
    """

    def __init__(self, db_path):
        self.storage = SqliteStorage(db_path)

    @staticmethod
    def _to_expense(row):
        return Expense(
            row[0], row[1], row[2], row[3],
            row[4], row[5], row[6], row[7], row[8],
        )

    def get_all(self, user_id):
        rows = self.storage.fetch_all(user_id)
        return [self._to_expense(row) for row in rows]

    def add(self, expense):
        new_id = self.storage.insert(
            expense.name,
            expense.amount_cents,
            expense.date,
            expense.category,
            expense.payment_type,
            expense.merchant,
            expense.note,
            expense.user_id,
        )
        expense.id = new_id

    def find_by_id(self, expense_id, user_id):
        row = self.storage.fetch_by_id(expense_id, user_id)

        if row is None:
            return None

        return self._to_expense(row)

    def get_highest(self, user_id):
        row = self.storage.fetch_highest(user_id)

        if row is None:
            return None

        return self._to_expense(row)

    def get_lowest(self, user_id):
        row = self.storage.fetch_lowest(user_id)

        if row is None:
            return None

        return self._to_expense(row)

    def get_top_month(self, user_id):
        return self.storage.fetch_top_month(user_id)

    def get_month_totals(self, user_id):
        return self.storage.fetch_month_totals(user_id)

    def get_top_weekday(self, user_id):
        row = self.storage.fetch_top_weekday(user_id)

        if row is None:
            return None

        # SQL gives back "0".."6"; the name is applied here so both
        # repositories answer with the same string.
        return (weekday_name(row[0]), row[1])

    def get_daily_totals(self, month, user_id):
        return self.storage.fetch_daily_totals(month, user_id)

    def count_by_name(self, name, user_id):
        return self.storage.count_by_name(name, user_id)

    def search_by_name(self, name, user_id):
        rows = self.storage.search_by_name(name, user_id)
        return [self._to_expense(row) for row in rows]

    def update(self, expense):
        self.storage.update(
            expense.id,
            expense.name,
            expense.amount_cents,
            expense.date,
            expense.category,
            expense.payment_type,
            expense.merchant,
            expense.note,
            expense.user_id,
        )

    def delete(self, expense):
        self.storage.delete(expense.id, expense.user_id)

    def delete_all(self, user_id):
        return self.storage.delete_all(user_id)

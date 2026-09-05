from app.repositories.expense_repository import ExpenseRepository
from app.models.expense import Expense
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

    def get_all(self):
        rows = self.storage.fetch_all()
        return [Expense(row[0], row[1], row[2]) for row in rows]

    def add(self, expense):
        new_id = self.storage.insert(expense.name, expense.amount)
        expense.id = new_id

    def find_by_id(self, expense_id):
        row = self.storage.fetch_by_id(expense_id)

        if row is None:
            return None

        return Expense(row[0], row[1], row[2])

    def update(self, expense):
        self.storage.update(expense.id, expense.name, expense.amount)

    def delete(self, expense):
        self.storage.delete(expense.id)

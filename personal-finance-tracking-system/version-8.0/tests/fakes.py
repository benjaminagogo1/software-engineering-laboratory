from app.repositories.memory_expense_repository import MemoryExpenseRepository


class FakeRepository(MemoryExpenseRepository):
    """
    The in-memory repository, plus handles the tests assert against.

    Reusing MemoryExpenseRepository rather than reimplementing it keeps the
    analytics logic in one place; the SQLite version is what pins the behaviour
    down, so the two implementations stay honest relative to each other.
    """

    def __init__(self):
        super().__init__()
        self.add_expense = None
        self.delete_expense = None

    def add(self, expense):
        super().add(expense)
        self.add_expense = expense

    def delete(self, expense):
        super().delete(expense)
        self.delete_expense = expense

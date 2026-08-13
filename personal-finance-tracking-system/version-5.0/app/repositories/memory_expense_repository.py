
from app.repositories.expense_repository import ExpenseRepository


class MemoryExpenseRepository(ExpenseRepository):

    def __init__(self):
        self.expenses = []
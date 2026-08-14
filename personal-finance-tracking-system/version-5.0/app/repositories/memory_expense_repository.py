
from app.repositories.expense_repository import ExpenseRepository


class MemoryExpenseRepository(ExpenseRepository):

    def __init__(self):
        self.expenses = []


    def get_all(self):
        return self.expenses

    
    def add(self, expense):
        ids = [expense.id for expense in self.expenses]

        next_id = max(ids, default=0) + 1

        expense.id = next_id

        self.expenses.append(expense)


    def find_by_id(self, expense_id):
        for expense in self.expenses:
            if expense.id == expense_id:
                return expense

        return None
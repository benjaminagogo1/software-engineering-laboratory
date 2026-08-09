print("first")
from app.repositories.expense_repository import ExpenseRepository
from app.storage.json_storage import JsonStorage
from app.models.expense import Expense

class JsonExpenseRepository(ExpenseRepository):

    def __init__(self):
        self.storage = JsonStorage()
        self.expenses = []

    def add(self, expense):
        self.expenses.append(expense)

    def save(self, expense):
        data = []

        for expense in self.expenses:
            data.append({
                "name": expense.name,
                "amount": expense.amount
            })

        self.storage.save(data)


    def get_all(self):
        data = self.storage.load()

        self.expenses = []

        for item in data:
            expense = Expense(
            item["name"],
            item["amount"]
        )
        self.expenses.append(expense)

        return self.expenses

    def find_by_name(self, name):
        print("Finding expense")

    def delete(self, expense):
        print("Deleting expense")


repository = JsonExpenseRepository()


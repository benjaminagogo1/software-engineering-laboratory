from app.repositories.expense_repository import ExpenseRepository
from app.storage.json_storage import JsonStorage
from app.models.expense import Expense

class JsonExpenseRepository(ExpenseRepository):

    def __init__(self):
        self.storage = JsonStorage()
        self.expenses = []

    


    def get_all(self):
        data = self.storage.load()

        self.expenses = []

        for item in data:
            expense = Expense(
            item["id"],
            item["name"],
            item["amount"]
            )

            self.expenses.append(expense)

        return self.expenses
    


    def add(self, expense):
        expenses = self.get_all()

        ids = [expense.id for expense in expenses]

        next_id = max(ids, default=0) + 1

        expense.id = next_id

        self.expenses.append(expense)

    def find_by_id(self, expense_id):
        expenses = self.get_all()

        for expense in expenses:
            if expense.id == expense_id:
                return expense
            
        return None


    def update(self, expense):
        self.save()

    def delete(self, expense):
        self.expenses.remove(expense)
        self.save()

    def save(self):
        data = []

        for expense in self.expenses        :
            data.append({
                "id": expense.id,
                "name": expense.name,
                "amount": expense.amount
            })
        self.storage.save(data)
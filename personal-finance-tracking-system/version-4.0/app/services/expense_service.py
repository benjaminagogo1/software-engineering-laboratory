from app.models.expense import Expense
from app.repositories.json_expense_repository import JsonExpenseRepository

class ExpenseService:

    def __init__(self, repository):
        self.repository = repository

    def add_expense(self, expense):
        self.repository.add(expense)
        return self.repository.save()
    

    def get_all_expense(self):
        return self.repository.get_all()
    



    def search_expenses(self, name):
        expenses = self.repository.get_all()

        matches = []

        for expense in expenses:
            if name.strip().lower() in expense.name.lower():
                matches.append(expense)

        return matches
    
    def update_expense(self, expense, amount):
        expense.amount = amount
        return self.repository.save()
    

    def add_expense(self, expense):
        self.repository.add(expense)
        return self.repository.save()
    


repository = JsonExpenseRepository()
service = ExpenseService(repository)


expense = Expense("Transport", 500)

service.add_expense(expense)
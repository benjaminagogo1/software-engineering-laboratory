from app.services.results import UpdateResult
from app.services.results import AddResult


class ExpenseService:

    def __init__(self, repository):
        self.repository = repository

    def add_expense(self, expense):
        if not expense.name.strip():
            return AddResult.INVALID_NAME

        if expense.amount <= 0:
            return AddResult.INVALID_AMOUNT

        self.repository.add(expense)

        return AddResult.SUCCESS
    
    def get_all_expenses(self):
        return self.repository.get_all()

    def get_expense_by_id(self, expense_id):
        return self.repository.find_by_id(expense_id)
    

    def delete_expense_by_id(self, expense_id):
        expense = self.repository.find_by_id(expense_id)

        if expense is None:
            return False

        self.repository.delete(expense)
        return True
    

    def update_expense(self, expense_id, amount):
        if amount <= 0:
            return UpdateResult.INVALID_AMOUNT

        expense = self.repository.find_by_id(expense_id)

        if expense is None:
            return UpdateResult.NOT_FOUND

        expense.amount = amount
        self.repository.update(expense)

        return UpdateResult.SUCCESS
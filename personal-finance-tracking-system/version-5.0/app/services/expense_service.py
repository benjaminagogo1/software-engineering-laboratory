class ExpenseService:

    def __init__(self, repository):
        self.repository = repository

    def add_expense(self, expense):
        self.repository.add(expense)

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
        expense = self.repository.find_by_id(expense_id)

        if expense is None:
            return False

        expense.amount = amount
        self.repository.update(expense)

        return True
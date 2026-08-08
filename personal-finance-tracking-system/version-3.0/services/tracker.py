from models.expense import Expense

class ExpenseTracker:
    def __init__(self, storage):
        self.storage = storage
        self.expenses = storage.load()

    def add_expense(self, expense):
        self.expenses.append(expense)

        if not self.storage.save_expense(self.expenses):
            self.expenses.remove(expense)
            return False
        return True


    def show_expense(self):
        if len(self.expenses) == 0:
            print("No expense saved.")
            return
        for expense in self.expenses:
            print(expense.name, expense.amount, expense.date)

    def delete_expense(self, expense):
        try:
            self.expenses.remove(expense)
            self.storage.save_expense(self.expenses)
            return True
        except ValueError:
            return False


    def search_expense(self, name):
        name = name.strip().lower()

        matches = []

        for expense in self.expenses:
            if name in expense.name.lower():
                matches.append(expense)

        return matches


    def update_expense(self, expense, amount):
        expense.amount = amount

        if not self.storage.save_expense(self.expenses):
            return False

        return True
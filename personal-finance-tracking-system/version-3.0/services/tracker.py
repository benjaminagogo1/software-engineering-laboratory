from models.expense import Expense

class ExpenseTracker:
    def __init__(self, storage):
        self.storage = storage
        self.expenses = storage.load()

    def add_expense(self, expense):
        self.expenses.append(expense)
        self.storage.save_expense(self.expenses)


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
        for expense in self.expenses:
            if expense.name == name:
                return expense
                
        return None
        
    def update_expense(self, name, amount):
        expense = self.search_expense(name)
        if expense is None:
            return False
        expense.amount = amount
        self.storage.save_expense(self.expenses)
        return True
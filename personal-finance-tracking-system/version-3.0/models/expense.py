
class Expense:
    def __init__(self, name, amount, date):
        if not name.strip():
            raise ValueError("Expense name can not be empty.")
        if amount <= 0:
            raise ValueError("Expense amount must be greater than zero.")
        self.name = name
        self.amount = amount
        self.date = date
        
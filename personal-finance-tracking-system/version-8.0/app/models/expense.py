


class Expense:
    def __init__(self, expense_id, name, amount, user_id):
        self.id = expense_id
        self.name = name
        self.amount = amount
        self.user_id = user_id

    def __eq__(self, other):
        if not isinstance(other, Expense):
            return False
        
        return (
            self.id == other.id
            and self.name == other.name
            and self.amount == other.amount
            and self.user_id == other.user_id
        )
from app.models.expense import Expense


def add_expense_menu(service):
    name = input("Enter expense name: ")
    amount = float(input("Enter expense amount: "))

    expense = Expense(name, amount)

    service.add_expense(expense)

    print("Expense added successfully.")
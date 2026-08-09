from app.models.expense import Expense


def add_expense_menu(service):
    name = input("Enter expense name: ")
    amount = float(input("Enter expense amount: "))

    expense = Expense(name, amount)
    service.add_expense(expense)

    print("Expense added successfully.")


def show_expenses_menu(service):
    expenses = service.get_all_expenses()

    if not expenses:
        print("No expenses found.")
        return

    for expense in expenses:
        print(f"Name: {expense.name}")
        print(f"Amount: {expense.amount}")
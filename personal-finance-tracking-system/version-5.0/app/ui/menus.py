from app.services.results import UpdateResult, AddResult, DeleteResult
from app.models.expense import Expense

def add_expense_menu(service):
    name = input("Enter expense name: ")

    amount_input = input("Enter expense amount: ")

    try:
        amount = float(amount_input)
    except ValueError:
        print("Invalid amount. Please enter a number.")
        return

    from app.models.expense import Expense

    expense = Expense(None, name, amount)

    result = service.add_expense(expense)

    if result == AddResult.SUCCESS:
        print("Expense added successfully.")

    elif result == AddResult.INVALID_NAME:
        print("Expense name cannot be empty.")

    elif result == AddResult.INVALID_AMOUNT:
        print("Amount must be greater than zero.")

def show_expenses_menu(service):
    expenses = service.get_all_expenses()

    if not expenses:
        print("No expenses found.")
        return

    for expense in expenses:
        print(f"ID: {expense.id}")
        print(f"Name: {expense.name}")
        print(f"Amount: {expense.amount}")
        print()


def search_expenses_menu(service):
    name = input("Enter expense name: ")

    matches = service.search_expenses(name)

    if not matches:
        print("No matching expenses found.")
        return

    for expense in matches:
        print(f"ID: {expense.id}")
        print(f"Name: {expense.name}")
        print(f"Amount: {expense.amount}")
        print()




def update_expense_menu(service):
    expense_id_input = input("Enter expense ID to update: ")

    try:
        expense_id = int(expense_id_input)
    except ValueError:
        print("Invalid expense ID. Please enter a number.")
        return

    amount_input = input("Enter new amount: ")

    try:
        amount = float(amount_input)
    except ValueError:
        print("Invalid amount. Please enter a number.")
        return

    result = service.update_expense(expense_id, amount)

    if result == UpdateResult.SUCCESS:
        print("Expense updated successfully.")

    elif result == UpdateResult.NOT_FOUND:
        print("Expense not found.")

    elif result == UpdateResult.INVALID_AMOUNT:
        print("Amount must be greater than zero.")


def delete_expense_menu(service):
    try:
        expense_id = int(input("Enter expense ID to delete: "))
    except ValueError:
        print("Invalid expense ID. Please enter a number.")
        return
    result = service.delete_expense_by_id(expense_id)

    if result == DeleteResult.SUCCESS:
        print("Expense deleted successfully.")

    elif result == DeleteResult.NOT_FOUND:
        print("Expense not found.")
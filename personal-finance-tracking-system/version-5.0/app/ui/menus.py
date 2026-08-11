def add_expense_menu(service):
    name = input("Enter expense name: ")
    amount = float(input("Enter expense amount: "))

    from app.models.expense import Expense

    expense = Expense(None, name, amount)

    service.add_expense(expense)

    print("Expense added successfully.")


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
    try:
        expense_id = int(input("Enter expense ID to update: "))
    except ValueError:
        print("Invalid expense ID. Please enter a number.")
        return
    try:
        amount = float(input("Enter new amount: "))
    except ValueError:
        print("Invalid input. Please enter a number.")
        return
    updated = service.update_expense(expense_id, amount)

    if updated:
        print("Expense updated successfully.")
    else:
        print("Expense not found.")


def delete_expense_menu(service):
    try:
        expense_id = int(input("Enter expense ID to delete: "))
    except ValueError:
        print("Invalid expense ID. Please enter a number.")
        return
    deleted = service.delete_expense_by_id(expense_id)

    if deleted:
        print("Expense deleted successfully.")
    else:
        print("Expense not found.")
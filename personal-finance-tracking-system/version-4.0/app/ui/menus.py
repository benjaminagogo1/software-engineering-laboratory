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



def search_expenses_menu(service):
    name = input("Enter expense name: ")

    matches = service.search_expenses(name)

    if not matches:
        print("No matching expenses found.")
        return

    for expense in matches:
        print(f"Name: {expense.name}")
        print(f"Amount: {expense.amount}")




def update_expense_menu(service):
    name = input("Enter expense name to update: ")

    matches = service.search_expenses(name)

    if not matches:
        print("No matching expenses found.")
        return

    expense = matches[0]

    amount = float(input("Enter new amount: "))

    service.update_expense(expense, amount)

    print("Expense updated successfully.")




def delete_expense_menu(service):
    name = input("Enter expense name to delete: ")

    matches = service.search_expenses(name)

    if not matches:
        print("No matching expenses found.")
        return

    expense = matches[0]

    service.delete_expense(expense)

    print("Expense deleted successfully.")
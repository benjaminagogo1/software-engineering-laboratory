print("menus.py is executing...")
from datetime import datetime

from models.expense import Expense



def add_expense_menu(tracker):
    name = input("Enter expense name ")
    date = input("Enter the date: ")
    try:
        date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        print("Invalid date. Use YYYY-MM-DD.")
        return
    
    try:
        amount = int(input("Enter expense amount "))
    except ValueError:
        print("Please, only digits are allowed.")
        return  
    
    try:
        expense = Expense(name, amount, date)
    except ValueError as error:
        print(error)
        return
    print(type(expense.date))
    tracker.add_expense(expense)
    print(f"Expense: '{expense.name}' added successfully!")



def show_expense_menu(tracker):
    tracker.show_expense()



def search_expense_menu(tracker):
    name = input("Enter expense name: ")
    matches = tracker.search_expense(name)
    if not matches:
        print(f"Item '{name}' was not found.")
        return
    for expense in matches:
        print(f"Name: {expense.name}")
        print(f"Amount: {expense.amount}")
        print(f"Date: {expense.date}")

def update_expense_menu(tracker):
    name = input("Enter expense name to update: ")

    matches = tracker.search_expense(name)

    if not matches:
        print(f"Item '{name}' was not found.")
        return

    print("\nMatching expenses:")

    for index, expense in enumerate(matches, start=1):
        print(
            f"{index}. {expense.name} - "
            f"{expense.amount} - {expense.date}"
        )

    try:
        choice = int(input("Choose an expense: "))
    except ValueError:
        print("Invalid choice. Please enter a number.")
        return

    if choice < 1 or choice > len(matches):
        print("Invalid expense selection.")
        return

    selected_expense = matches[choice - 1]

    try:
        amount = int(input("Enter new amount: "))
    except ValueError:
        print("Please, only digits are allowed.")
        return

    if amount <= 0:
        print("Amount must be greater than zero.")
        return

    if tracker.update_expense(selected_expense, amount):
        print(
            f"Expense '{selected_expense.name}' "
            "updated successfully."
        )
    else:
        print("Unable to update expense.")
def delete_expense_menu(tracker):
    name = input("Enter expense name: ")
    expense = tracker.search_expense(name)
    if expense is None:
        print("Expense is not found.")
        return
    else:
        print("Expense found.")
        print(expense.name, expense.amount, expense.date)
    print("Are you sure?  (yes/no)")
    choice = input("Enter your choice. ").lower()
    if choice == "yes":  
        tracker.delete_expense(expense)
        print(f"Expense '{expense.name}' deleted successfully!")
    else:
        print("Deletion cancelled")
    

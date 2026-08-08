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
    tracker.add_expense(expense)
    print(f"Expense: '{expense.name}' added successfully!")



def show_expense_menu(tracker):
    tracker.show_expense()



def search_expense_menu(tracker):
    name = input("Enter expense name: ")
    expense = tracker.search_expense(name)
    if expense is None:
        print("Expense is not found. ")
    else:
        print(expense.name, expense.amount, expense.date)



def update_expense_menu(tracker):
    name = input("Enter expense name: ")
    expense = tracker.search_expense(name)
    if expense is None:
        print("Expense not found.")
        return
    else:
        print("Expense found.")
        print(expense.name, expense.amount, expense.date)
    try:
        amount = int(input("Enter new amount: "))
    except ValueError:
        print("Error: Please, only digits are allowed.")
        return
    tracker.update_expense(name, amount)
    print(f"Expense '{expense.name}' updated successfully!")
   


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
    

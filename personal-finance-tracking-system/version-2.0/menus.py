from models import Expense




def add_expense_menu(tracker):
    name = input("Enter expense name ")
    try:
        amount = int(input("Enter expense amount "))
    except ValueError:
        print("Please, only digits are allowed.")
        return  

    expense = Expense(name, amount)
    tracker.add_expense(expense)
    print(f"Expense: '{expense.name}' added successfully!'")



def show_expense_menu(tracker):
    tracker.show_expense()



def search_expense_menu(tracker):
    name = input("Enter expense name: ")
    expense = tracker.search_expense(name)
    if expense is None:
        print("Expense is not found. ")
    else:
        print(expense.name, expense.amount)





def update_expense_menu(tracker):
    name = input("Enter expense name: ")
    expense = tracker.search_expense(name)
    if expense is None:
        print("Expense not found.")
        return
    else:
        print("Expense found.")
        print(expense.name, expense.amount)
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
        print(expense.name, expense.amount)
    print("Are you sure?  (yes/no)")
    choice = input("Enter your choice. ").lower()
    if choice == "yes":  
        tracker.delete_expense(expense)
        print(f"Expense '{expense.name}' deleted successfully!")
    else:
        print("Deletion cancelled")
    

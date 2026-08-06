from storage import load_expense
from tracker import ExpenseTracker
import menus



tracker = ExpenseTracker()
   
# def main():
    # tracker.expenses = load_expense()


# main()
running = True
while running:
    print("\nExpense Tracker")
    print("1. Add Expense")
    print("2. Show Expense")
    print("3. Search Expense")
    print("4. Update Expense")
    print("5. Delete Expense")
    print("6. Exit")

    try:
        choice = int(input("Choose an option:  "))
    except ValueError:
        print("Invalid input: Please, only digits are allowed.")
        continue
    if choice == 1:
        menus.add_expense_menu(tracker)

    if choice == 2:
        menus.show_expense_menu(tracker)

    if choice == 3:
        menus.search_expense_menu(tracker)

    if choice == 4:
        menus.update_expense_menu(tracker)

    if choice == 5:
        menus.delete_expense_menu(tracker)

    if choice == 6:
        running = False

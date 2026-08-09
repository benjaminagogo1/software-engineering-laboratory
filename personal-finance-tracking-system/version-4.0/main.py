from app.repositories.json_expense_repository import JsonExpenseRepository
from app.services.expense_service import ExpenseService
from app.ui.menus import add_expense_menu, show_expenses_menu


def main():
    repository = JsonExpenseRepository()
    service = ExpenseService(repository)

    while True:
        print("\nExpense Tracker")
        print("1. Add Expense")
        print("2. Show Expenses")
        print("3. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            add_expense_menu(service)

        elif choice == "2":
            show_expenses_menu(service)

        elif choice == "3":
            break

        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
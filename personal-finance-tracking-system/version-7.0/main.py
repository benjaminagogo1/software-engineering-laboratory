from config import setup_logging
import config
from app.repositories.sqlite_expense_repository import SqliteExpenseRepository
from app.services.expense_service import ExpenseService

from app.ui.menus import (
    add_expense_menu,
    show_expenses_menu,
    update_expense_menu,
    delete_expense_menu,
)



logger = setup_logging()
logger.info("Application started")



def main():
    repository = SqliteExpenseRepository(config.DB_PATH)
    service = ExpenseService(repository)

    while True:
        print("\nExpense Tracker")
        print("1. Add Expense")
        print("2. Show Expenses")
        print("3. Update Expense")
        print("4. Delete Expense")
        print("5. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            add_expense_menu(service)

        elif choice == "2":
            show_expenses_menu(service)

        elif choice == "3":
            update_expense_menu(service)

        elif choice == "4":
            delete_expense_menu(service)

        elif choice == "5":
            break

        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()

from app.auth.policy import WeakCredentials
from app.logging_config import setup_logging
import sys
import getpass
import config
from app.repositories.sqlite_audit_repository import SqliteAuditRepository
from app.repositories.sqlite_expense_repository import SqliteExpenseRepository
from app.repositories.sqlite_user_repository import SqliteUserRepository
from app.services.expense_service import ExpenseService
from app.services.user_service import UserService
from cli.commands import run

from app.ui.menus import (
    add_expense_menu,
    show_expenses_menu,
    update_expense_menu,
    delete_expense_menu,
    delete_all_expenses_menu,
    search_expenses_menu,
    top_month_menu,
    months_menu,
    top_day_menu,
    highest_expense_menu,
    lowest_expense_menu,
    frequency_menu,
    chart_menu,
)



logger = setup_logging()
logger.info("Application started")



def login_prompt(user_service):
    """
    Asks the user to log in or register before the menu opens.

    Returns the authenticated User, or None if the user chose to exit. The
    password is read with getpass so it never lands in the terminal history.
    """
    while True:
        print("\n1. Login")
        print("2. Register")
        print("3. Exit")

        choice = input("Choose an option: ")

        if choice == "3":
            return None

        if choice not in ("1", "2"):
            print("Invalid option.")
            continue

        username = input("Username: ")
        password = getpass.getpass("Password: ")

        if choice == "2":
            # The policy refuses a weak pair by raising, so the loop continues
            # rather than the program ending — this is a menu someone is
            # already inside, and a rejected password is a prompt to try again.
            try:
                user = user_service.register_user(username, password)
            except WeakCredentials as refused:
                print(refused)
                continue

            if user is None:
                print("Username already exists.")
                continue

            print(f"Welcome, {user.username}.")
            return user

        user = user_service.authenticate(username, password)

        if user is None:
            print("Invalid username or password.")
            continue

        print(f"Welcome back, {user.username}.")
        return user


def main():
    repository = SqliteExpenseRepository(config.DB_PATH)

    audit = SqliteAuditRepository(config.DB_PATH, source="cli")

    service = ExpenseService(repository, audit)

    user_repository = SqliteUserRepository(config.DB_PATH)
    user_service = UserService(user_repository, audit)

    if len(sys.argv) > 1:
        run(service, user_service)
        return

    user = login_prompt(user_service)

    if user is None:
        return

    while True:
        print("\nExpense Tracker")
        print("1. Add Expense")
        print("2. Show Expenses")
        print("3. Update Expense")
        print("4. Delete Expense")
        print("5. Delete All Expenses")
        print("6. Search Expenses")
        print("7. Highest Spending Month")
        print("8. Compare Months")
        print("9. Highest Spending Day of the Week")
        print("10. Highest Spending Expense")
        print("11. Lowest Spending Expense")
        print("12. Expense Frequency")
        print("13. Spending Chart (HTML)")
        print("14. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            add_expense_menu(service, user.id)

        elif choice == "2":
            show_expenses_menu(service, user.id)

        elif choice == "3":
            update_expense_menu(service, user.id)

        elif choice == "4":
            delete_expense_menu(service, user.id)

        elif choice == "5":
            delete_all_expenses_menu(service, user.id)

        elif choice == "6":
            search_expenses_menu(service, user.id)

        elif choice == "7":
            top_month_menu(service, user.id)

        elif choice == "8":
            months_menu(service, user.id)

        elif choice == "9":
            top_day_menu(service, user.id)

        elif choice == "10":
            highest_expense_menu(service, user.id)

        elif choice == "11":
            lowest_expense_menu(service, user.id)

        elif choice == "12":
            frequency_menu(service, user.id)

        elif choice == "13":
            chart_menu(service, user.id)

        elif choice == "14":
            break

        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()

from app.repositories.json_expense_repository import JsonExpenseRepository
from app.services.expense_service import ExpenseService
from app.ui.menus import add_expense_menu


def main():
    repository = JsonExpenseRepository()
    service = ExpenseService(repository)

    add_expense_menu(service)


if __name__ == "__main__":
    main()
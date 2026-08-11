from app.repositories.json_expense_repository import JsonExpenseRepository
from app.services.expense_service import ExpenseService


def main():
    repository = JsonExpenseRepository()
    service = ExpenseService(repository)

    updated = service.update_expense(1, 750)

    if updated:
        print("Expense updated successfully.")
    else:
        print("Expense not found.")


if __name__ == "__main__":
    main()
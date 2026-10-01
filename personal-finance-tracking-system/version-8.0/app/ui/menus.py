from app.services.results import UpdateResult, AddResult, DeleteResult
from app.ui.input_helpers import (
    read_int,
    read_amount_cents,
    read_date,
    read_choice,
    read_month,
)
from app.ui.formatting import AMOUNT_RULE, format_money
from app.models.expense import Expense, CATEGORIES, PAYMENT_TYPES
from app.reports.monthly_chart import write_monthly_spending
from app.storage.storage_error import StorageError
import config


def print_expense(expense):
    """Shows every attribute an expense carries."""
    print(f"ID: {expense.id}")
    print(f"Name: {expense.name}")
    print(f"Amount: {format_money(expense.amount_cents)}")
    print(f"Date: {expense.date}")
    print(f"Category: {expense.category}")
    print(f"Payment type: {expense.payment_type}")
    print(f"Merchant: {expense.merchant or '-'}")
    print(f"Note: {expense.note or '-'}")
    print()


def _read_optional(prompt):
    """
    Free text where a blank answer means "leave it as it is", so the update
    menu doesn't force the user to retype a note to change an amount.
    """
    value = input(prompt).strip()

    return value or None


def add_expense_menu(service, user_id):
    name = input("Enter expense name: ")

    amount_cents = read_amount_cents("Enter expense amount: ")

    if amount_cents is None:
        return

    expense_date = read_date("Enter expense date (YYYY-MM-DD, blank for today): ")

    if expense_date is None:
        return

    category = read_choice("Enter category (blank for Other): ", CATEGORIES)

    if category is None:
        return

    payment_type = read_choice("Enter payment type (blank for Other): ", PAYMENT_TYPES)

    if payment_type is None:
        return

    merchant = _read_optional("Enter merchant (optional): ")
    note = _read_optional("Enter note (optional): ")

    expense = Expense(
        None, name, amount_cents, user_id, expense_date, category, payment_type, merchant, note
    )

    result = service.add_expense(expense)

    if result == AddResult.SUCCESS:
        print("Expense added successfully.")

    elif result == AddResult.INVALID_NAME:
        print("Expense name cannot be empty.")

    elif result == AddResult.INVALID_AMOUNT:
        print(AMOUNT_RULE)

    elif result == AddResult.INVALID_CATEGORY:
        print(f"Category must be one of: {', '.join(CATEGORIES)}")

    elif result == AddResult.INVALID_PAYMENT_TYPE:
        print(f"Payment type must be one of: {', '.join(PAYMENT_TYPES)}")

def show_expenses_menu(service, user_id):
    try:
        expenses = service.get_all_expenses(user_id)

    except StorageError:
        print("Unable to load expenses. Storage is corrupted.")
        return

    if not expenses:
        print("No expenses found.")
        return

    for expense in expenses:
        print_expense(expense)


def search_expenses_menu(service, user_id):
    name = input("Enter expense name to search for: ")

    try:
        matches = service.search_by_name(name, user_id)

    except StorageError:
        print("Unable to load expenses. Storage is corrupted.")
        return

    if not matches:
        print("No matching expenses found.")
        return

    for expense in matches:
        print_expense(expense)




def update_expense_menu(service, user_id):
    expense_id = read_int("Enter expense ID to update: ")

    if expense_id is None:
        return

    amount_cents = read_amount_cents("Enter new amount: ")

    if amount_cents is None:
        return

    merchant = _read_optional("Enter merchant (blank to keep unchanged): ")
    note = _read_optional("Enter note (blank to keep unchanged): ")

    result = service.update_expense(
        expense_id, amount_cents, user_id, merchant=merchant, note=note
    )

    if result == UpdateResult.SUCCESS:
        print("Expense updated successfully.")

    elif result == UpdateResult.NOT_FOUND:
        print("Expense not found.")

    elif result == UpdateResult.INVALID_AMOUNT:
        print(AMOUNT_RULE)


def delete_expense_menu(service, user_id):
    expense_id = read_int("Enter expense ID to delete: ")

    if expense_id is None:
        return

    result = service.delete_expense_by_id(expense_id, user_id)

    if result == DeleteResult.SUCCESS:
        print("Expense deleted successfully.")

    elif result == DeleteResult.NOT_FOUND:
        print("Expense not found.")


def delete_all_expenses_menu(service, user_id):
    """
    Clears the signed-in user's expense list. Asks for the word "yes" rather
    than a single keypress: this is the one action here that can't be undone,
    and only your own expenses are in scope.
    """
    try:
        existing = service.get_all_expenses(user_id)

    except StorageError:
        print("Unable to load expenses. Storage is corrupted.")
        return

    if not existing:
        print("No expenses found.")
        return

    print(f"This deletes all {len(existing)} of your expenses. It cannot be undone.")
    confirmation = input('Type "yes" to confirm: ').strip().lower()

    if confirmation != "yes":
        print("Cancelled. Nothing was deleted.")
        return

    deleted = service.delete_all_expenses(user_id)

    print(f"Deleted {deleted} expense(s).")


def top_month_menu(service, user_id):
    try:
        top_month = service.get_top_month(user_id)

    except StorageError:
        print("Unable to load expenses. Storage is corrupted.")
        return

    if top_month is None:
        print("No expenses found.")
        return

    month, total = top_month

    print(f"Highest spending month: {month}")
    print(f"Total: {format_money(total)}")


def months_menu(service, user_id):
    """Every month's total, highest first, with a bar so they compare at a glance."""
    try:
        totals = service.get_month_totals(user_id)

    except StorageError:
        print("Unable to load expenses. Storage is corrupted.")
        return

    if not totals:
        print("No expenses found.")
        return

    largest = totals[0][1]
    width = max(len(month) for month, _ in totals)

    for month, total in totals:
        # Proportional to the biggest month, so the ranking is visible without
        # reading every number.
        filled = max(1, round(total / largest * 24))
        print(f"{month:<{width}}  {'█' * filled} {format_money(total)}")


def top_day_menu(service, user_id):
    try:
        top_day = service.get_top_weekday(user_id)

    except StorageError:
        print("Unable to load expenses. Storage is corrupted.")
        return

    if top_day is None:
        print("No expenses found.")
        return

    day, total = top_day

    print(f"Highest spending day of the week: {day}")
    print(f"Total: {format_money(total)}")


def highest_expense_menu(service, user_id):
    try:
        expense = service.get_highest_expense(user_id)

    except StorageError:
        print("Unable to load expenses. Storage is corrupted.")
        return

    if expense is None:
        print("No expenses found.")
        return

    print("Highest spending expense:")
    print_expense(expense)


def lowest_expense_menu(service, user_id):
    try:
        expense = service.get_lowest_expense(user_id)

    except StorageError:
        print("Unable to load expenses. Storage is corrupted.")
        return

    if expense is None:
        print("No expenses found.")
        return

    print("Lowest spending expense:")
    print_expense(expense)


def frequency_menu(service, user_id):
    name = input("Enter expense name: ")

    try:
        count = service.count_by_name(name, user_id)

    except StorageError:
        print("Unable to load expenses. Storage is corrupted.")
        return

    print(f"{name} appears {count} time(s).")


def chart_menu(service, user_id):
    """Writes the month's spending graph to an HTML file and says where."""
    month = read_month("Enter month (YYYY-MM, blank for this month): ")

    if month is None:
        return

    try:
        daily_totals = service.get_daily_totals(month, user_id)

    except StorageError:
        print("Unable to load expenses. Storage is corrupted.")
        return

    path = write_monthly_spending(month, daily_totals, config.REPORTS_DIR)

    print(f"Chart written to {path}")
    print("Open that file in a browser to view it.")

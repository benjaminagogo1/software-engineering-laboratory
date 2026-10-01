import datetime

from app.repositories.expense_repository import ExpenseRepository
from app.models.expense import weekday_name


class MemoryExpenseRepository(ExpenseRepository):
    """
    The in-memory implementation. Every method here has to agree with
    SqliteExpenseRepository down to the tie-breaks, because tests use this one
    to pin the analytics logic while the SQLite version is what actually runs.
    """

    def __init__(self):
        self.expenses = []

    def get_all(self, user_id):
        return [
            expense for expense in self.expenses
            if expense.user_id == user_id
        ]

    def add(self, expense):
        ids = [expense.id for expense in self.expenses]

        next_id = max(ids, default=0) + 1

        expense.id = next_id

        self.expenses.append(expense)

    def find_by_id(self, expense_id, user_id):
        for expense in self.expenses:
            if expense.id == expense_id and expense.user_id == user_id:
                return expense

        return None

    def get_highest(self, user_id):
        owned = self.get_all(user_id)

        if not owned:
            return None

        # Highest amount wins; the lower id breaks a tie, matching the
        # ORDER BY amount_cents DESC, id ASC the SQLite repository uses.
        return max(owned, key=lambda expense: (expense.amount_cents, -expense.id))

    def get_lowest(self, user_id):
        owned = self.get_all(user_id)

        if not owned:
            return None

        # Same tie-break as get_highest, at the other end: ORDER BY
        # amount_cents ASC, id ASC.
        return min(owned, key=lambda expense: (expense.amount_cents, expense.id))

    def _month_totals(self, user_id):
        totals = {}

        for expense in self.get_all(user_id):
            month = expense.date[:7]
            # Seeded with an int, not 0.0: these totals are kobo and SUM()
            # over the same rows returns an integer, so a float here would be
            # the one place the two repositories disagree about the type.
            totals[month] = totals.get(month, 0) + expense.amount_cents

        return totals

    def get_month_totals(self, user_id):
        totals = self._month_totals(user_id)

        # Month descending first, then a stable sort by total descending —
        # the equivalent of SQL's ORDER BY total DESC, month DESC.
        months = sorted(totals, reverse=True)
        months.sort(key=lambda month: totals[month], reverse=True)

        return [(month, totals[month]) for month in months]

    def get_top_month(self, user_id):
        totals = self.get_month_totals(user_id)

        # Defined as the head of the ranking rather than computed separately,
        # so the two can never disagree about which month won.
        return totals[0] if totals else None

    def get_top_weekday(self, user_id):
        totals = {}

        for expense in self.get_all(user_id):
            # Python numbers weekdays from Monday; strftime('%w') and the
            # WEEKDAYS tuple start at Sunday.
            weekday = (datetime.date.fromisoformat(expense.date).weekday() + 1) % 7
            totals[weekday] = totals.get(weekday, 0) + expense.amount_cents

        if not totals:
            return None

        # Highest total wins; the earlier weekday breaks a tie, matching
        # ORDER BY total DESC, weekday ASC.
        weekday = max(totals, key=lambda number: (totals[number], -number))

        return (weekday_name(weekday), totals[weekday])

    def get_daily_totals(self, month, user_id):
        totals = {}

        for expense in self.get_all(user_id):
            if expense.date[:7] != month:
                continue

            totals[expense.date] = totals.get(expense.date, 0) + expense.amount_cents

        return sorted(totals.items())

    def count_by_name(self, name, user_id):
        target = name.lower()

        return sum(
            1 for expense in self.get_all(user_id)
            if expense.name.lower() == target
        )

    def search_by_name(self, name, user_id):
        term = name.lower()

        return [
            expense for expense in self.get_all(user_id)
            if term in expense.name.lower()
        ]

    def update(self, expense):
        for index, existing in enumerate(self.expenses):
            if existing.id == expense.id:
                self.expenses[index] = expense
                return

    def delete(self, expense):
        if expense in self.expenses:
            self.expenses.remove(expense)

    def delete_all(self, user_id):
        owned = self.get_all(user_id)

        self.expenses = [
            expense for expense in self.expenses
            if expense.user_id != user_id
        ]

        return len(owned)

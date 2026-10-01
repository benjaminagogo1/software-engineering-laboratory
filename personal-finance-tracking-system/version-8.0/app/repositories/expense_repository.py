from abc import ABC, abstractmethod
from app.models.expense import Expense


class ExpenseRepository(ABC):

    @abstractmethod
    def add(self, expense):
        pass

    @abstractmethod
    def get_all(self, user_id) -> list[Expense]:
        pass

    @abstractmethod
    def find_by_id(self, expense_id, user_id) -> Expense | None:
        pass

    @abstractmethod
    def get_highest(self, user_id) -> Expense | None:
        """The single most expensive expense for this user."""

    @abstractmethod
    def get_lowest(self, user_id) -> Expense | None:
        """The single cheapest expense for this user."""

    @abstractmethod
    def get_top_month(self, user_id) -> tuple[str, float] | None:
        """The month with the highest total spending, as ("YYYY-MM", total)."""

    @abstractmethod
    def get_month_totals(self, user_id) -> list[tuple[str, float]]:
        """
        Every month's total spending as ("YYYY-MM", total), highest first.

        A superset of get_top_month: its first entry is that same month, so a
        caller can compare months instead of only seeing the winner.
        """

    @abstractmethod
    def get_top_weekday(self, user_id) -> tuple[str, float] | None:
        """The weekday with the highest total spending, as (name, total)."""

    @abstractmethod
    def get_daily_totals(self, month, user_id) -> list[tuple[str, float]]:
        """
        Per-day totals within `month` ("YYYY-MM") as ("YYYY-MM-DD", total).

        Only days with spending appear; filling the month's empty days is left
        to whoever is drawing the result.
        """

    @abstractmethod
    def count_by_name(self, name, user_id) -> int:
        """How many times this expense name occurs, ignoring case."""

    @abstractmethod
    def search_by_name(self, name, user_id) -> list[Expense]:
        """Every expense whose name contains `name`, ignoring case."""

    @abstractmethod
    def update(self, expense):
        pass

    @abstractmethod
    def delete(self, expense):
        pass

    @abstractmethod
    def delete_all(self, user_id) -> int:
        """Deletes every expense this user owns, returning how many were removed."""

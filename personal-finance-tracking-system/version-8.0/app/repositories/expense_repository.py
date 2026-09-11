from abc import ABC, abstractmethod
from app.models.expense import Expense


class ExpenseRepository(ABC):

    @abstractmethod
    def add(self, expense):
        pass

    @abstractmethod
    def get_all(self) -> list[Expense]:
        pass

    @abstractmethod
    def find_by_id(self, expense_id) -> Expense | None:
        pass

    @abstractmethod
    def update(self, expense):
        pass

    @abstractmethod
    def delete(self, expense):
        pass


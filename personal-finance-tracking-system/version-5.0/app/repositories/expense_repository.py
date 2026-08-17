from abc import ABC, abstractmethod


class ExpenseRepository(ABC):

    @abstractmethod
    def add(self, expense):
        pass

    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def find_by_id(self, expense_id):
        pass

    @abstractmethod
    def update(self, expense):
        pass

    @abstractmethod
    def delete(self, expense):
        pass

  
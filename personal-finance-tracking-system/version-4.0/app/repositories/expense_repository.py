from abc import ABC, abstractmethod


class ExpenseRepository(ABC):

    @abstractmethod
    def add(self, expense):
        pass

    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def get_all_expenses(self):
        pass


    @abstractmethod
    def update(self, expense):
        pass

    @abstractmethod
    def delete(self, expense):
        pass

    
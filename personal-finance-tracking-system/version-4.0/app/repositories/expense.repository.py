from abc import ABC, abstractmethod


class ExpenseRepository(ABC):

    @abstractmethod
    def save(self, expense):
        pass

    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def find_by_name(self, name):
        pass

    @abstractmethod
    def delete(self, expense):
        pass
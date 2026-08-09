from abc import ABC, abstractmethod


class ExpenseRepository(ABC):

    @abstractmethod
    def add(self, expense):
        pass

    @abstractmethod
    def save(self):
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
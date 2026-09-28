from abc import ABC, abstractmethod
from app.models.user import User


class UserRepository(ABC):

      @abstractmethod

      def add(self, user):
            pass

      @abstractmethod
      def find_by_username(self, username) -> User | None:
            pass
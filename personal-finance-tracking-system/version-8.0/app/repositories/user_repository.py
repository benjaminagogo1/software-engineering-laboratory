from abc import ABC, abstractmethod
from app.models.user import User


class UserRepository(ABC):

      @abstractmethod

      def add(self, user):
            pass

      @abstractmethod
      def find_by_username(self, username) -> User | None:
            pass

      @abstractmethod
      def find_by_id(self, user_id) -> User | None:
            """Used to render the signed-in user; the id comes from the token."""
            pass
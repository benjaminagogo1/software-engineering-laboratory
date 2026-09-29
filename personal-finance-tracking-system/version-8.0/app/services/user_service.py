
from app.auth.jwt import create_access_token

from app.auth.password import verify_password



from app.auth.password import hash_password
from app.models.user import User


class UserService:
    def __init__(self, repository):
        self.repository = repository

    def register_user(self, username, password):
      existing_user = self.repository.find_by_username(username)

      if existing_user is not None:
            return None

      password_hash = hash_password(password)

      user = User(None, username, password_hash)

      self.repository.add(user)

      return user


    def login_user(self, username, password):
            user = self.repository.find_by_username(username)

            if user is None:
                  return None

            if not verify_password(password, user.password_hash):
                  return None

            token = create_access_token(user.id)

            return token
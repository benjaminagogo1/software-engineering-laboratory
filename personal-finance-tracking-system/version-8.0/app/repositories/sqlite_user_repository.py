from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.storage.sqlite_storage import SqliteStorage


class SqliteUserRepository(UserRepository):
    def __init__(self, db_path):
        self.storage = SqliteStorage(db_path)

    def add(self, user):
        new_id = self.storage.insert_user(
            user.username,
            user.password_hash
        )
        user.id = new_id

    def find_by_username(self, username):
        row = self.storage.fetch_user_by_username(username)

        if row is None:
            return None

        return User(row[0], row[1], row[2])

    def find_by_id(self, user_id):
        row = self.storage.fetch_user_by_id(user_id)

        if row is None:
            return None

        return User(row[0], row[1], row[2])
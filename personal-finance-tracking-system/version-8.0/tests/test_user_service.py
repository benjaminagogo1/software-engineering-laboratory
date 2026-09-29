from app.services.user_service import UserService


class FakeUserRepository:
    def __init__(self):
        self.users = []

    def find_by_username(self, username):
        for user in self.users:
            if user.username == username:
                return user
        return None

    def add(self, user):
        user.id = len(self.users) + 1
        self.users.append(user)


def test_register_user():
    repository = FakeUserRepository()
    service = UserService(repository)

    user = service.register_user(
        "benjamin",
        "TestPassword123"
    )
    assert user is not None
    assert user.id == 1
    assert user.username == "benjamin"
    assert user.password_hash.startswith("$argon2id$")


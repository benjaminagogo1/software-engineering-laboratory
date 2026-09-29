from app.models.user import User
from app.repositories.sqlite_user_repository import SqliteUserRepository


def test_add_and_find_user(tmp_path):
    repository = SqliteUserRepository(tmp_path / "test.db")

    user = User(
        None,
        "benjamin",
        "test-password-hash"
    )

    repository.add(user)

    found_user = repository.find_by_username("benjamin")

    assert found_user is not None
    assert found_user.id == user.id
    assert found_user.username == "benjamin"
    assert found_user.password_hash == "test-password-hash"
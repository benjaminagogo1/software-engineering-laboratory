CREDENTIALS = {
    "username": "api_user",
    "password": "TestPassword123"
}


def test_register_user(client):
    response = client.post("/register", json=CREDENTIALS)

    assert response.status_code == 201

    data = response.json()

    assert data["id"] is not None
    assert data["username"] == "api_user"


def test_login_user(client):
    register_response = client.post("/register", json=CREDENTIALS)

    assert register_response.status_code == 201

    login_response = client.post("/login", json=CREDENTIALS)

    assert login_response.status_code == 200

    data = login_response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)


def test_password_is_hashed_at_rest(client, repositories):
    client.post("/register", json=CREDENTIALS)

    _, user_repository = repositories
    user = user_repository.find_by_username("api_user")

    assert user.password_hash != CREDENTIALS["password"]
    assert user.password_hash.startswith("$argon2id$")

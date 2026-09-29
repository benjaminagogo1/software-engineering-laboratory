from fastapi.testclient import TestClient

from app.api import app


client = TestClient(app)


def test_register_user():
    response = client.post(
        "/register",
        json={
            "username": "api_user",
            "password": "TestPassword123"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] is not None
    assert data["username"] == "api_user"







def test_login_user():
    register_response = client.post(
        "/register",
        json={
            "username": "login_user",
            "password": "TestPassword123"
        }
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/login",
        json={
            "username": "login_user",
            "password": "TestPassword123"
        }
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
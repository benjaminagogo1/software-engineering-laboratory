"""
The routes that serve the browser client.

The built frontend is not committed — `frontend/dist/` is generated — so these
assert the contract rather than the contents: that the client's routes are not
shadowed by the API's, and that not having built it yet fails clearly instead of
breaking the API.
"""

import pytest
from fastapi.testclient import TestClient

import config
from app.api import app


client = TestClient(app)


def test_the_root_sends_the_browser_to_the_client():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/app/"


def test_the_api_docs_survive_the_client_mount():
    """The catch-all is registered last, so it cannot swallow these."""
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200


def test_the_api_routes_still_win_over_the_client():
    """
    /expenses is both an API route and a page in the client. The API keeps it,
    which is why the client lives under /app.
    """
    assert client.get("/expenses").status_code == 401


def test_an_unbuilt_client_explains_itself():
    if (config.FRONTEND_DIST / "index.html").exists():
        pytest.skip("the frontend is built, so this path is unreachable")

    response = client.get("/app/expenses")

    assert response.status_code == 503
    assert "npm run build" in response.json()["detail"]

from fastapi.testclient import TestClient
from main import app
from routes.auth import verify_token


client = TestClient(app)


def fake_user():
    return "test@example.com"


app.dependency_overrides[verify_token] = fake_user


def test_invalid_payload():

    response = client.post(
        "/analyze-bug",
        json={
            "description": "",
            "language": "Python",
            "severity": "high"
        }
    )

    assert response.status_code == 422

    body = response.json()

    assert "error" in body
    assert "request_id" in body
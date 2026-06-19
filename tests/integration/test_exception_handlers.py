import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestExceptionHandlers:
    def test_401_response_format(self, client: TestClient):
        response = client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "unauthorized"

    def test_403_response_format(self, client: TestClient, cliente_auth_headers: dict):
        response = client.get("/usuarios", headers=cliente_auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "forbidden"

    def test_404_response_format(self, client: TestClient):
        response = client.get("/nonexistent-route")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "not_found"

    def test_422_validation_error_format(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={"email": "invalid"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "validation_error"
        assert "details" in data["error"]
        assert isinstance(data["error"]["details"], list)

    def test_422_multiple_errors(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert len(data["error"]["details"]) > 0

    def test_health_endpoint_returns_200(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "ok"

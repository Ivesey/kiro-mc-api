"""Unit tests for app/main.py — application bootstrap and router registration."""

import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestAppInstance:
    """Test that the FastAPI app instance is properly configured."""

    def test_app_exists(self):
        assert app is not None

    def test_app_title(self):
        assert app.title == "Case API"

    def test_app_version(self):
        assert app.version == "1.0.0"


class TestHealthCheck:
    """Test the root health check endpoint."""

    def test_get_root_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_get_root_returns_status_ok(self):
        response = client.get("/")
        assert response.json() == {"status": "ok"}


class TestDocEndpoints:
    """Test that auto-generated documentation endpoints are accessible."""

    def test_docs_returns_200(self):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_returns_200(self):
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_json_returns_200(self):
        response = client.get("/openapi.json")
        assert response.status_code == 200


class TestCasesRouterRegistered:
    """Test that the cases router is registered and endpoints are routable.

    Verifies routes don't return 405 Method Not Allowed, confirming registration.
    """

    def test_post_cases_is_routable(self):
        response = client.post(
            "/cases",
            json={
                "email": "test@example.com",
                "issue": "Test issue",
                "severity": "low",
            },
        )
        assert response.status_code == 201

    def test_get_cases_is_routable(self):
        response = client.get("/cases")
        assert response.status_code == 200

    def test_get_case_by_id_is_routable(self):
        case_id = str(uuid.uuid4())
        response = client.get(f"/cases/{case_id}")
        # 404 means the route exists but case doesn't — not 405
        assert response.status_code == 404

    def test_put_case_is_routable(self):
        case_id = str(uuid.uuid4())
        response = client.put(
            f"/cases/{case_id}",
            json={
                "email": "test@example.com",
                "issue": "Updated issue",
                "response": "",
                "severity": "medium",
            },
        )
        # 404 means the route exists but case doesn't — not 405
        assert response.status_code == 404

    def test_delete_case_is_routable(self):
        case_id = str(uuid.uuid4())
        response = client.delete(f"/cases/{case_id}")
        # 404 means the route exists but case doesn't — not 405
        assert response.status_code == 404

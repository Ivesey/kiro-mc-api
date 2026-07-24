"""Example-based endpoint tests for the cases router.

Validates: Requirements 3.1, 3.2, 3.4, 4.1, 4.2, 4.4, 5.1, 5.2, 5.3,
6.1, 6.2, 6.3, 6.5, 7.1, 7.2, 7.4, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6
"""

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_dal
from app.dal.in_memory_case_dal import InMemoryCaseDAL


@pytest.fixture()
def shared_dal():
    """Provide a shared InMemoryCaseDAL instance for tests needing persistence."""
    return InMemoryCaseDAL()


@pytest.fixture()
def client(shared_dal):
    """TestClient with a shared DAL override, cleaned up after each test."""
    app.dependency_overrides[get_dal] = lambda: shared_dal
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def valid_create_body():
    return {
        "email": "user@example.com",
        "issue": "Dashboard fails to load after login.",
        "response": "",
        "severity": "high",
    }


@pytest.fixture()
def valid_update_body():
    return {
        "email": "updated@example.com",
        "issue": "Updated issue description.",
        "response": "We deployed a fix.",
        "severity": "low",
    }


# ---------- POST /cases ----------


class TestCreateCase:
    def test_valid_body_returns_201_with_case_id(self, client, valid_create_body):
        resp = client.post("/cases", json=valid_create_body)
        assert resp.status_code == 201
        data = resp.json()
        # Should have a valid UUID case_id
        uuid.UUID(data["case_id"])
        assert data["email"] == valid_create_body["email"]
        assert data["issue"] == valid_create_body["issue"]
        assert data["response"] == valid_create_body["response"]
        assert data["severity"] == valid_create_body["severity"]

    def test_invalid_body_returns_422(self, client):
        # Missing required fields
        resp = client.post("/cases", json={})
        assert resp.status_code == 422

    def test_invalid_email_returns_422(self, client):
        resp = client.post("/cases", json={
            "email": "not-an-email",
            "issue": "Some issue",
            "severity": "low",
        })
        assert resp.status_code == 422

    def test_invalid_severity_returns_422(self, client):
        resp = client.post("/cases", json={
            "email": "user@example.com",
            "issue": "Some issue",
            "severity": "extreme",
        })
        assert resp.status_code == 422


# ---------- GET /cases ----------


class TestGetAllCases:
    def test_returns_200_with_list(self, client, valid_create_body):
        client.post("/cases", json=valid_create_body)
        resp = client.get("/cases")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_returns_empty_list_when_no_cases(self, client):
        resp = client.get("/cases")
        assert resp.status_code == 200
        assert resp.json() == []


# ---------- GET /cases/{id} ----------


class TestGetCaseById:
    def test_returns_200_for_existing_case(self, client, valid_create_body):
        create_resp = client.post("/cases", json=valid_create_body)
        case_id = create_resp.json()["case_id"]

        resp = client.get(f"/cases/{case_id}")
        assert resp.status_code == 200
        assert resp.json()["case_id"] == case_id

    def test_returns_404_for_non_existent_case(self, client):
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/cases/{fake_id}")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"]

    def test_returns_422_for_invalid_uuid(self, client):
        resp = client.get("/cases/not-a-uuid")
        assert resp.status_code == 422


# ---------- PUT /cases/{id} ----------


class TestUpdateCase:
    def test_returns_200_for_valid_update(self, client, valid_create_body, valid_update_body):
        create_resp = client.post("/cases", json=valid_create_body)
        case_id = create_resp.json()["case_id"]

        resp = client.put(f"/cases/{case_id}", json=valid_update_body)
        assert resp.status_code == 200
        data = resp.json()
        assert data["case_id"] == case_id
        assert data["email"] == valid_update_body["email"]
        assert data["issue"] == valid_update_body["issue"]
        assert data["response"] == valid_update_body["response"]
        assert data["severity"] == valid_update_body["severity"]

    def test_returns_404_for_non_existent_case(self, client, valid_update_body):
        fake_id = str(uuid.uuid4())
        resp = client.put(f"/cases/{fake_id}", json=valid_update_body)
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"]

    def test_returns_422_for_invalid_body(self, client, valid_create_body):
        create_resp = client.post("/cases", json=valid_create_body)
        case_id = create_resp.json()["case_id"]

        # Empty body — missing required fields
        resp = client.put(f"/cases/{case_id}", json={})
        assert resp.status_code == 422


# ---------- DELETE /cases/{id} ----------


class TestDeleteCase:
    def test_returns_204_for_existing_case(self, client, valid_create_body):
        create_resp = client.post("/cases", json=valid_create_body)
        case_id = create_resp.json()["case_id"]

        resp = client.delete(f"/cases/{case_id}")
        assert resp.status_code == 204

    def test_returns_404_for_non_existent_case(self, client):
        fake_id = str(uuid.uuid4())
        resp = client.delete(f"/cases/{fake_id}")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"]


# ---------- Error response format ----------


class TestErrorResponseFormat:
    def test_404_has_json_content_type(self, client):
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/cases/{fake_id}")
        assert resp.status_code == 404
        assert "application/json" in resp.headers["content-type"]

    def test_422_has_json_content_type(self, client):
        resp = client.post("/cases", json={})
        assert resp.status_code == 422
        assert "application/json" in resp.headers["content-type"]


# ---------- DAL exception mapping ----------


class TestDALExceptionMapping:
    """Test that DAL exceptions are correctly mapped to HTTP status codes."""

    def _make_client_with_mock_dal(self, mock_dal):
        app.dependency_overrides[get_dal] = lambda: mock_dal
        client = TestClient(app)
        return client

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_value_error_returns_400(self):
        mock_dal = MagicMock()
        mock_dal.create_case.side_effect = ValueError("Invalid value provided")
        client = self._make_client_with_mock_dal(mock_dal)

        resp = client.post("/cases", json={
            "email": "user@example.com",
            "issue": "Test issue",
            "severity": "low",
        })
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid value provided"
        assert "application/json" in resp.headers["content-type"]

    def test_type_error_returns_422(self):
        mock_dal = MagicMock()
        mock_dal.create_case.side_effect = TypeError("Wrong type for field")
        client = self._make_client_with_mock_dal(mock_dal)

        resp = client.post("/cases", json={
            "email": "user@example.com",
            "issue": "Test issue",
            "severity": "low",
        })
        assert resp.status_code == 422
        assert resp.json()["detail"] == "Wrong type for field"
        assert "application/json" in resp.headers["content-type"]

    def test_unexpected_exception_returns_500_with_fixed_message(self):
        mock_dal = MagicMock()
        mock_dal.create_case.side_effect = RuntimeError("DB connection lost: secret-host:5432")
        client = self._make_client_with_mock_dal(mock_dal)

        resp = client.post("/cases", json={
            "email": "user@example.com",
            "issue": "Test issue",
            "severity": "low",
        })
        assert resp.status_code == 500
        assert resp.json()["detail"] == "An internal error occurred"
        # Must NOT leak the internal exception message
        assert "secret-host" not in resp.text
        assert "application/json" in resp.headers["content-type"]

    def test_get_all_unexpected_exception_returns_500(self):
        mock_dal = MagicMock()
        mock_dal.get_all_cases.side_effect = RuntimeError("unexpected")
        client = self._make_client_with_mock_dal(mock_dal)

        resp = client.get("/cases")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "An internal error occurred"

    def test_get_by_id_value_error_returns_400(self):
        mock_dal = MagicMock()
        mock_dal.get_case_by_id.side_effect = ValueError("bad value")
        client = self._make_client_with_mock_dal(mock_dal)

        case_id = str(uuid.uuid4())
        resp = client.get(f"/cases/{case_id}")
        assert resp.status_code == 400
        assert resp.json()["detail"] == "bad value"

    def test_update_type_error_returns_422(self):
        mock_dal = MagicMock()
        mock_dal.update_case.side_effect = TypeError("type mismatch")
        client = self._make_client_with_mock_dal(mock_dal)

        case_id = str(uuid.uuid4())
        resp = client.put(f"/cases/{case_id}", json={
            "email": "user@example.com",
            "issue": "Updated issue",
            "response": "Fixed",
            "severity": "medium",
        })
        assert resp.status_code == 422
        assert resp.json()["detail"] == "type mismatch"

    def test_delete_unexpected_exception_returns_500(self):
        mock_dal = MagicMock()
        mock_dal.delete_case.side_effect = OSError("disk failure")
        client = self._make_client_with_mock_dal(mock_dal)

        case_id = str(uuid.uuid4())
        resp = client.delete(f"/cases/{case_id}")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "An internal error occurred"
        assert "disk failure" not in resp.text

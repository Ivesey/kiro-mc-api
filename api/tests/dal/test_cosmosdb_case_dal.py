"""Unit tests for CosmosDBCaseDAL implementation."""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.models.case import CaseModel
from azure.cosmos.exceptions import (
    CosmosResourceExistsError,
    CosmosResourceNotFoundError,
)


def _make_case(**overrides) -> CaseModel:
    """Helper to create a valid CaseModel with sensible defaults."""
    defaults = {
        "case_id": uuid.uuid4(),
        "email": "test@example.com",
        "issue": "Something broke",
        "response": "We are looking into it.",
        "severity": "medium",
    }
    defaults.update(overrides)
    return CaseModel(**defaults)


def _build_dal():
    """Create a CosmosDBCaseDAL with mocked dependencies, return (dal, mock_container)."""
    mock_settings = MagicMock()
    mock_settings.cosmosdb_endpoint = "https://test.documents.azure.com:443/"
    mock_settings.cosmosdb_key = "dGVzdGtleQ=="
    mock_settings.cosmosdb_database_name = "test-db"
    mock_settings.cosmosdb_container_name = "test-container"

    mock_container = MagicMock()
    mock_database = MagicMock()
    mock_database.get_container_client.return_value = mock_container

    mock_client_instance = MagicMock()
    mock_client_instance.get_database_client.return_value = mock_database

    with patch(
        "azure_dal.cosmosdb_case_dal.get_settings", return_value=mock_settings
    ), patch(
        "azure_dal.cosmosdb_case_dal.CosmosClient", return_value=mock_client_instance
    ):
        from azure_dal.cosmosdb_case_dal import CosmosDBCaseDAL

        dal = CosmosDBCaseDAL()

    return dal, mock_container


class TestInitialization:
    """Tests for CosmosDBCaseDAL initialization."""

    def test_missing_endpoint_raises_runtime_error(self):
        """RuntimeError raised when cosmosdb_endpoint is empty."""
        mock_settings = MagicMock()
        mock_settings.cosmosdb_endpoint = ""
        mock_settings.cosmosdb_key = "dGVzdGtleQ=="

        with patch(
            "azure_dal.cosmosdb_case_dal.get_settings", return_value=mock_settings
        ):
            from azure_dal.cosmosdb_case_dal import CosmosDBCaseDAL

            with pytest.raises(RuntimeError, match="COSMOSDB_ENDPOINT"):
                CosmosDBCaseDAL()

    def test_missing_key_raises_runtime_error(self):
        """RuntimeError raised when cosmosdb_key is empty."""
        mock_settings = MagicMock()
        mock_settings.cosmosdb_endpoint = "https://test.documents.azure.com:443/"
        mock_settings.cosmosdb_key = ""

        with patch(
            "azure_dal.cosmosdb_case_dal.get_settings", return_value=mock_settings
        ):
            from azure_dal.cosmosdb_case_dal import CosmosDBCaseDAL

            with pytest.raises(RuntimeError, match="COSMOSDB_KEY"):
                CosmosDBCaseDAL()

    def test_valid_settings_initializes_successfully(self):
        """DAL initializes when valid endpoint and key are configured."""
        dal, _ = _build_dal()
        assert dal._container is not None


class TestCreateCase:
    """Tests for create_case method."""

    def test_create_case_returns_case(self):
        """create_case returns the same CaseModel on success."""
        dal, mock_container = _build_dal()
        case = _make_case()

        result = dal.create_case(case)

        assert result == case
        mock_container.create_item.assert_called_once()

    def test_create_case_duplicate_raises_value_error(self):
        """create_case raises ValueError when case_id already exists."""
        dal, mock_container = _build_dal()
        case = _make_case()

        mock_container.create_item.side_effect = CosmosResourceExistsError()

        with pytest.raises(ValueError, match="already exists"):
            dal.create_case(case)


class TestGetCaseById:
    """Tests for get_case_by_id method."""

    def test_get_case_by_id_returns_case(self):
        """get_case_by_id returns deserialized CaseModel on success."""
        dal, mock_container = _build_dal()
        case = _make_case()
        item = {
            "id": str(case.case_id),
            "case_id": str(case.case_id),
            "email": case.email,
            "issue": case.issue,
            "response": case.response,
            "severity": case.severity,
        }
        mock_container.read_item.return_value = item

        result = dal.get_case_by_id(case.case_id)

        assert result.case_id == case.case_id
        assert result.email == case.email
        assert result.issue == case.issue
        assert result.response == case.response
        assert result.severity == case.severity
        mock_container.read_item.assert_called_once_with(
            item=str(case.case_id), partition_key=str(case.case_id)
        )

    def test_get_case_by_id_not_found_raises_key_error(self):
        """get_case_by_id raises KeyError when case does not exist."""
        dal, mock_container = _build_dal()
        case_id = uuid.uuid4()

        mock_container.read_item.side_effect = CosmosResourceNotFoundError()

        with pytest.raises(KeyError):
            dal.get_case_by_id(case_id)


class TestUpdateCase:
    """Tests for update_case method."""

    def test_update_case_returns_updated_case(self):
        """update_case returns the CaseModel on success."""
        dal, mock_container = _build_dal()
        case = _make_case()
        item = {
            "id": str(case.case_id),
            "case_id": str(case.case_id),
            "email": case.email,
            "issue": case.issue,
            "response": case.response,
            "severity": case.severity,
        }
        mock_container.read_item.return_value = item

        result = dal.update_case(case.case_id, case)

        assert result == case
        mock_container.replace_item.assert_called_once()

    def test_update_case_not_found_raises_key_error(self):
        """update_case raises KeyError when case does not exist."""
        dal, mock_container = _build_dal()
        case_id = uuid.uuid4()
        case = _make_case(case_id=case_id)

        mock_container.read_item.side_effect = CosmosResourceNotFoundError()

        with pytest.raises(KeyError):
            dal.update_case(case_id, case)


class TestDeleteCase:
    """Tests for delete_case method."""

    def test_delete_case_succeeds(self):
        """delete_case calls delete_item on the container."""
        dal, mock_container = _build_dal()
        case_id = uuid.uuid4()

        dal.delete_case(case_id)

        mock_container.delete_item.assert_called_once_with(
            item=str(case_id), partition_key=str(case_id)
        )

    def test_delete_case_not_found_raises_key_error(self):
        """delete_case raises KeyError when case does not exist."""
        dal, mock_container = _build_dal()
        case_id = uuid.uuid4()

        mock_container.delete_item.side_effect = CosmosResourceNotFoundError()

        with pytest.raises(KeyError):
            dal.delete_case(case_id)


class TestGetAllCases:
    """Tests for get_all_cases method."""

    def test_get_all_cases_returns_deserialized_list(self):
        """get_all_cases returns a list of deserialized CaseModels."""
        dal, mock_container = _build_dal()
        case1 = _make_case(severity="low")
        case2 = _make_case(severity="high")
        items = [
            {
                "id": str(case1.case_id),
                "case_id": str(case1.case_id),
                "email": case1.email,
                "issue": case1.issue,
                "response": case1.response,
                "severity": case1.severity,
            },
            {
                "id": str(case2.case_id),
                "case_id": str(case2.case_id),
                "email": case2.email,
                "issue": case2.issue,
                "response": case2.response,
                "severity": case2.severity,
            },
        ]
        mock_container.query_items.return_value = iter(items)

        result = dal.get_all_cases()

        assert len(result) == 2
        assert result[0].case_id == case1.case_id
        assert result[0].severity == "low"
        assert result[1].case_id == case2.case_id
        assert result[1].severity == "high"

    def test_get_all_cases_empty_returns_empty_list(self):
        """get_all_cases returns empty list when no cases exist."""
        dal, mock_container = _build_dal()
        mock_container.query_items.return_value = iter([])

        result = dal.get_all_cases()

        assert result == []


class TestSerialization:
    """Tests for serialization/deserialization round-trip."""

    def test_serialize_deserialize_preserves_all_fields(self):
        """Serialization followed by deserialization preserves all fields."""
        dal, _ = _build_dal()
        case = _make_case(
            case_id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
            email="roundtrip@example.com",
            issue="Round-trip test issue",
            response="Round-trip test response",
            severity="critical",
        )

        serialized = dal._serialize(case)
        deserialized = dal._deserialize(serialized)

        assert deserialized.case_id == case.case_id
        assert deserialized.email == case.email
        assert deserialized.issue == case.issue
        assert deserialized.response == case.response
        assert deserialized.severity == case.severity

    def test_serialize_produces_expected_keys(self):
        """Serialized dict contains expected keys with correct types."""
        dal, _ = _build_dal()
        case = _make_case()

        serialized = dal._serialize(case)

        assert "id" in serialized
        assert "case_id" in serialized
        assert "email" in serialized
        assert "issue" in serialized
        assert "response" in serialized
        assert "severity" in serialized
        assert serialized["id"] == str(case.case_id)
        assert serialized["case_id"] == str(case.case_id)

"""Unit tests for CaseDAL ABC and InMemoryCaseDAL implementation."""

import ast
import inspect
import uuid

import pytest

from app.dal import CaseDAL, InMemoryCaseDAL
from app.models.case import CaseModel


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


# --- ABC enforcement ---


class TestABCEnforcement:
    def test_incomplete_subclass_raises_type_error(self):
        """An incomplete subclass of CaseDAL cannot be instantiated."""

        class IncompleteDal(CaseDAL):
            pass

        with pytest.raises(TypeError):
            IncompleteDal()


# --- Empty store ---


class TestEmptyStore:
    def test_get_all_cases_returns_empty_list(self):
        dal = InMemoryCaseDAL()
        assert dal.get_all_cases() == []


# --- create_case ---


class TestCreateCase:
    def test_create_case_persists_and_returns_matching_model(self):
        dal = InMemoryCaseDAL()
        case = _make_case()
        result = dal.create_case(case)

        assert result == case
        assert dal.get_case_by_id(case.case_id) == case

    def test_create_case_raises_value_error_on_duplicate(self):
        dal = InMemoryCaseDAL()
        case = _make_case()
        dal.create_case(case)

        with pytest.raises(ValueError):
            dal.create_case(case)


# --- update_case ---


class TestUpdateCase:
    def test_update_case_replaces_stored_case(self):
        dal = InMemoryCaseDAL()
        case = _make_case()
        dal.create_case(case)

        updated = _make_case(case_id=case.case_id, issue="Updated issue")
        result = dal.update_case(case.case_id, updated)

        assert result == updated
        assert dal.get_case_by_id(case.case_id) == updated

    def test_update_case_raises_key_error_for_nonexistent_id(self):
        dal = InMemoryCaseDAL()
        case = _make_case()

        with pytest.raises(KeyError):
            dal.update_case(case.case_id, case)

    def test_update_case_raises_value_error_when_case_id_is_none(self):
        dal = InMemoryCaseDAL()
        case = _make_case()

        with pytest.raises(ValueError):
            dal.update_case(None, case)

    def test_update_case_raises_value_error_when_case_is_none(self):
        dal = InMemoryCaseDAL()
        case = _make_case()
        dal.create_case(case)

        with pytest.raises(ValueError):
            dal.update_case(case.case_id, None)


# --- delete_case ---


class TestDeleteCase:
    def test_delete_case_removes_case_from_store(self):
        dal = InMemoryCaseDAL()
        case = _make_case()
        dal.create_case(case)

        dal.delete_case(case.case_id)

        assert dal.get_all_cases() == []
        with pytest.raises(KeyError):
            dal.get_case_by_id(case.case_id)

    def test_delete_case_raises_key_error_for_nonexistent_id(self):
        dal = InMemoryCaseDAL()

        with pytest.raises(KeyError):
            dal.delete_case(uuid.uuid4())

    def test_delete_case_raises_value_error_when_case_id_is_none(self):
        dal = InMemoryCaseDAL()

        with pytest.raises(ValueError):
            dal.delete_case(None)


# --- get_case_by_id ---


class TestGetCaseById:
    def test_get_case_by_id_returns_correct_case(self):
        dal = InMemoryCaseDAL()
        case = _make_case()
        dal.create_case(case)

        result = dal.get_case_by_id(case.case_id)
        assert result == case

    def test_get_case_by_id_raises_key_error_for_nonexistent_id(self):
        dal = InMemoryCaseDAL()

        with pytest.raises(KeyError):
            dal.get_case_by_id(uuid.uuid4())

    def test_get_case_by_id_raises_type_error_when_case_id_is_none(self):
        dal = InMemoryCaseDAL()

        with pytest.raises(TypeError):
            dal.get_case_by_id(None)

    def test_get_case_by_id_raises_type_error_when_case_id_is_non_uuid(self):
        dal = InMemoryCaseDAL()

        with pytest.raises(TypeError):
            dal.get_case_by_id("not-a-uuid")


# --- Module exports ---


class TestModuleExports:
    def test_import_case_dal_and_in_memory_case_dal(self):
        """Verify that CaseDAL and InMemoryCaseDAL are importable from app.dal."""
        from app.dal import CaseDAL, InMemoryCaseDAL

        assert inspect.isclass(CaseDAL)
        assert inspect.isclass(InMemoryCaseDAL)

    def test_no_router_or_http_imports_in_case_dal(self):
        """case_dal.py must not import any router or HTTP modules."""
        import app.dal.case_dal as module

        source_path = inspect.getfile(module)
        with open(source_path, "r") as f:
            tree = ast.parse(f.read())

        forbidden = {"fastapi", "starlette", "httpx", "requests"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in forbidden, (
                        f"Forbidden import found: {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert node.module.split(".")[0] not in forbidden, (
                        f"Forbidden import found: {node.module}"
                    )

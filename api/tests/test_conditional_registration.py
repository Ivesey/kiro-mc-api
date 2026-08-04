"""Unit tests for conditional DynamoDBCaseDAL registration in dependencies.py.

Requirements: 4.1, 4.2, 4.4, 4.5, 4.6, 4.7
"""

import importlib
import sys
from types import ModuleType
from unittest.mock import patch, MagicMock

import pytest

from app.dal.case_dal import CaseDAL


class TestConditionalRegistration:
    """Tests for the conditional import/registration of DynamoDBCaseDAL."""

    def _reload_dependencies(self):
        """Reload dependencies module to re-execute module-level import logic."""
        import app.dependencies
        importlib.reload(app.dependencies)
        return app.dependencies

    def test_aws_dal_importable_registers_dynamodb_dal(self):
        """Requirement 4.1: when aws_dal is importable, DynamoDBCaseDAL appears in DAL_REGISTRY."""
        # Create a mock DynamoDBCaseDAL class
        mock_dal_class = MagicMock(spec=type)
        mock_dal_class.__name__ = "DynamoDBCaseDAL"

        # Create mock modules for aws_dal and aws_dal.dynamodb_case_dal
        mock_aws_dal = ModuleType("aws_dal")
        mock_dynamodb_module = ModuleType("aws_dal.dynamodb_case_dal")
        mock_dynamodb_module.DynamoDBCaseDAL = mock_dal_class

        modules_patch = {
            "aws_dal": mock_aws_dal,
            "aws_dal.dynamodb_case_dal": mock_dynamodb_module,
        }

        with patch.dict(sys.modules, modules_patch):
            deps = self._reload_dependencies()
            assert "DynamoDBCaseDAL" in deps.DAL_REGISTRY
            assert deps.DAL_REGISTRY["DynamoDBCaseDAL"] is mock_dal_class

    def test_aws_dal_not_importable_registry_unchanged(self):
        """Requirement 4.2, 4.6: when aws_dal is not importable, DAL_REGISTRY is unchanged, no exception."""
        # Setting a sys.modules entry to None causes ImportError on import attempt.
        # We need to block both 'aws_dal' and 'aws_dal.dynamodb_case_dal'.
        blocked_modules = {
            "aws_dal": None,
            "aws_dal.dynamodb_case_dal": None,
        }
        # Also include any other aws_dal submodules that may already be cached
        for key in list(sys.modules.keys()):
            if key.startswith("aws_dal"):
                blocked_modules[key] = None

        with patch.dict(sys.modules, blocked_modules):
            deps = self._reload_dependencies()
            # Should only contain InMemoryCaseDAL
            assert "InMemoryCaseDAL" in deps.DAL_REGISTRY
            assert "DynamoDBCaseDAL" not in deps.DAL_REGISTRY

    def test_aws_dal_importable_but_class_missing_registry_unchanged(self):
        """Requirement 4.7: when package importable but class missing (AttributeError), registry unchanged."""
        # Create a mock aws_dal module WITHOUT DynamoDBCaseDAL attribute
        mock_aws_dal = ModuleType("aws_dal")
        mock_dynamodb_module = ModuleType("aws_dal.dynamodb_case_dal")
        # Intentionally NOT setting mock_dynamodb_module.DynamoDBCaseDAL

        modules_patch = {
            "aws_dal": mock_aws_dal,
            "aws_dal.dynamodb_case_dal": mock_dynamodb_module,
        }

        with patch.dict(sys.modules, modules_patch):
            deps = self._reload_dependencies()
            assert "InMemoryCaseDAL" in deps.DAL_REGISTRY
            assert "DynamoDBCaseDAL" not in deps.DAL_REGISTRY


class TestGetDalWithDynamoDB:
    """Tests for get_dal behavior with DynamoDBCaseDAL configuration."""

    def test_get_dal_returns_dynamodb_dal_when_configured_and_importable(self):
        """Requirement 4.4: get_dal returns DynamoDBCaseDAL instance when configured and importable."""
        # Create a concrete mock class that behaves as a CaseDAL subclass
        class FakeDynamoDBCaseDAL(CaseDAL):
            def create_case(self, case):
                pass

            def update_case(self, case_id, case):
                pass

            def delete_case(self, case_id):
                pass

            def get_all_cases(self):
                return []

            def get_case_by_id(self, case_id):
                pass

        import app.dependencies
        # Manually add to registry for this test
        app.dependencies.DAL_REGISTRY["DynamoDBCaseDAL"] = FakeDynamoDBCaseDAL

        try:
            mock_settings = MagicMock()
            mock_settings.dal_implementation = "DynamoDBCaseDAL"

            with patch("app.dependencies.get_settings", return_value=mock_settings):
                dal = app.dependencies.get_dal()
                assert isinstance(dal, FakeDynamoDBCaseDAL)
        finally:
            del app.dependencies.DAL_REGISTRY["DynamoDBCaseDAL"]

    def test_get_dal_raises_value_error_when_configured_but_not_importable(self):
        """Requirement 4.5: get_dal raises ValueError when configured but not importable."""
        import app.dependencies

        # Ensure DynamoDBCaseDAL is NOT in the registry
        app.dependencies.DAL_REGISTRY.pop("DynamoDBCaseDAL", None)

        mock_settings = MagicMock()
        mock_settings.dal_implementation = "DynamoDBCaseDAL"

        with patch("app.dependencies.get_settings", return_value=mock_settings):
            with pytest.raises(ValueError, match="Unrecognized DAL implementation"):
                app.dependencies.get_dal()

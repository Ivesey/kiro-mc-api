"""Unit tests for app/config.py and app/dependencies.py (DI configuration).

Requirements: 2.1, 2.2, 2.5
"""

from unittest.mock import patch, MagicMock

import pytest

from app.config import AppSettings, get_settings
from app.dependencies import DAL_REGISTRY, get_dal, _reset_dal
from app.dal.case_dal import CaseDAL


class TestAppSettings:
    """Tests for AppSettings defaults and factory."""

    def test_default_dal_implementation_is_in_memory(self):
        """Requirement 2.2: default dal_implementation is InMemoryCaseDAL."""
        settings = get_settings()
        assert settings.dal_implementation == "InMemoryCaseDAL"

    def test_app_settings_direct_instantiation_default(self):
        """AppSettings without arguments defaults to InMemoryCaseDAL."""
        settings = AppSettings()
        assert settings.dal_implementation == "InMemoryCaseDAL"


class TestGetDal:
    """Tests for the get_dal provider function."""

    def setup_method(self):
        """Reset the DAL singleton before each test."""
        _reset_dal()

    def teardown_method(self):
        """Reset the DAL singleton after each test."""
        _reset_dal()

    def test_invalid_dal_name_raises_value_error(self):
        """Requirement 2.5: unrecognized DAL name raises ValueError."""
        mock_settings = MagicMock()
        mock_settings.dal_implementation = "NonExistentDAL"

        with patch("app.dependencies.get_settings", return_value=mock_settings):
            with pytest.raises(ValueError, match="Unrecognized DAL implementation"):
                get_dal()

    def test_custom_dal_registration(self):
        """Requirement 2.1: a custom DAL class registered in DAL_REGISTRY
        can be instantiated via get_dal()."""

        class CustomDAL(CaseDAL):
            """Minimal concrete DAL for testing custom registration."""

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

        # Temporarily add the custom DAL to the registry
        DAL_REGISTRY["CustomDAL"] = CustomDAL
        try:
            mock_settings = MagicMock()
            mock_settings.dal_implementation = "CustomDAL"

            with patch("app.dependencies.get_settings", return_value=mock_settings):
                dal = get_dal()
                assert isinstance(dal, CustomDAL)
        finally:
            # Clean up: remove the custom entry
            del DAL_REGISTRY["CustomDAL"]

    def test_default_settings_resolves_in_memory_dal(self):
        """get_dal() with default settings returns an InMemoryCaseDAL instance."""
        from app.dal.in_memory_case_dal import InMemoryCaseDAL

        dal = get_dal()
        assert isinstance(dal, InMemoryCaseDAL)

"""Unit tests for app/dependencies.py (DAL dynamic import).

Requirements: 2.1, 2.2, 2.5
"""

import os
from unittest.mock import patch

import pytest

from app.dependencies import get_dal, _reset_dal, _import_dal_class
from app.dal.case_dal import CaseDAL
from app.dal.in_memory_case_dal import InMemoryCaseDAL


class TestDefaultDal:
    """Tests for default DAL behavior."""

    def setup_method(self):
        _reset_dal()

    def teardown_method(self):
        _reset_dal()

    def test_default_dal_is_in_memory(self):
        """When DAL_IMPLEMENTATION is not set, get_dal returns InMemoryCaseDAL."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DAL_IMPLEMENTATION", None)
            dal = get_dal()
            assert isinstance(dal, InMemoryCaseDAL)

    def test_explicit_in_memory_dal_path(self):
        """Setting DAL_IMPLEMENTATION to the InMemoryCaseDAL path works."""
        with patch.dict(os.environ, {"DAL_IMPLEMENTATION": "app.dal.in_memory_case_dal.InMemoryCaseDAL"}):
            dal = get_dal()
            assert isinstance(dal, InMemoryCaseDAL)


class TestImportDalClass:
    """Tests for _import_dal_class validation."""

    def test_invalid_path_no_dot_raises_value_error(self):
        """A path without dots raises ValueError."""
        with pytest.raises(ValueError, match="dotted path"):
            _import_dal_class("NoDottedPath")

    def test_nonexistent_module_raises_value_error(self):
        """A path with a non-existent module raises ValueError."""
        with pytest.raises(ValueError, match="Could not import"):
            _import_dal_class("nonexistent.module.SomeClass")

    def test_nonexistent_class_raises_value_error(self):
        """A valid module but non-existent class raises ValueError."""
        with pytest.raises(ValueError, match="has no class"):
            _import_dal_class("app.dal.in_memory_case_dal.NonExistentClass")

    def test_non_casedal_subclass_raises_value_error(self):
        """A class that is not a CaseDAL subclass raises ValueError."""
        with pytest.raises(ValueError, match="not a CaseDAL subclass"):
            _import_dal_class("app.models.case.CaseModel")


class TestGetDalSingleton:
    """Tests for get_dal singleton behavior."""

    def setup_method(self):
        _reset_dal()

    def teardown_method(self):
        _reset_dal()

    def test_get_dal_returns_same_instance(self):
        """get_dal returns the same singleton instance on repeated calls."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DAL_IMPLEMENTATION", None)
            dal1 = get_dal()
            dal2 = get_dal()
            assert dal1 is dal2

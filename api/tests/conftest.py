"""Shared test fixtures."""

import pytest

from app.dependencies import _reset_dal


@pytest.fixture(autouse=True)
def reset_dal_singleton():
    """Reset the DAL singleton before and after each test to ensure isolation."""
    _reset_dal()
    yield
    _reset_dal()

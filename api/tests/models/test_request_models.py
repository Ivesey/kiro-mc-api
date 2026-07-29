"""Unit tests for request and error models.

Validates: Requirements 9.1, 9.2, 9.3, 9.5, 10.5
"""

import pytest
from pydantic import ValidationError

from app.models.requests import CreateCaseRequest, UpdateCaseRequest
from app.models.errors import ErrorResponse


# ---------------------------------------------------------------------------
# CreateCaseRequest tests
# ---------------------------------------------------------------------------


class TestCreateCaseRequest:
    """Tests for CreateCaseRequest model."""

    def test_valid_input_all_fields(self):
        """Valid input with all fields is accepted."""
        req = CreateCaseRequest(
            email="user@example.com",
            issue="Dashboard fails to load after login.",
            response="We are investigating.",
            severity="high",
        )
        assert req.email == "user@example.com"
        assert req.issue == "Dashboard fails to load after login."
        assert req.response == "We are investigating."
        assert req.severity == "high"

    def test_valid_input_response_defaults_to_empty(self):
        """When response is omitted, it defaults to empty string."""
        req = CreateCaseRequest(
            email="user@example.com",
            issue="Something broke.",
            severity="low",
        )
        assert req.response == ""

    def test_missing_email_raises_validation_error(self):
        """Missing required field email raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CreateCaseRequest(
                issue="Something broke.",
                severity="low",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("email",) for e in errors)

    def test_missing_issue_raises_validation_error(self):
        """Missing required field issue raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CreateCaseRequest(
                email="user@example.com",
                severity="low",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("issue",) for e in errors)

    def test_missing_severity_raises_validation_error(self):
        """Missing required field severity raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CreateCaseRequest(
                email="user@example.com",
                issue="Something broke.",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("severity",) for e in errors)

    def test_email_exceeds_254_chars_rejected(self):
        """Email exceeding 254 characters is rejected."""
        long_email = "a" * 246 + "@test.com"  # 255 chars total
        with pytest.raises(ValidationError) as exc_info:
            CreateCaseRequest(
                email=long_email,
                issue="Something broke.",
                severity="low",
            )
        errors = exc_info.value.errors()
        assert any("email" in str(e["loc"]) for e in errors)

    def test_email_without_at_rejected(self):
        """Email without @ symbol is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CreateCaseRequest(
                email="userexample.com",
                issue="Something broke.",
                severity="low",
            )
        errors = exc_info.value.errors()
        assert any("email" in str(e["loc"]) for e in errors)

    def test_issue_empty_string_rejected(self):
        """Empty issue string is rejected (min_length=1)."""
        with pytest.raises(ValidationError) as exc_info:
            CreateCaseRequest(
                email="user@example.com",
                issue="",
                severity="low",
            )
        errors = exc_info.value.errors()
        assert any("issue" in str(e["loc"]) for e in errors)

    def test_issue_exceeds_2000_chars_rejected(self):
        """Issue exceeding 2000 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CreateCaseRequest(
                email="user@example.com",
                issue="x" * 2001,
                severity="low",
            )
        errors = exc_info.value.errors()
        assert any("issue" in str(e["loc"]) for e in errors)

    def test_response_exceeds_5000_chars_rejected(self):
        """Response exceeding 5000 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CreateCaseRequest(
                email="user@example.com",
                issue="Something broke.",
                response="r" * 5001,
                severity="low",
            )
        errors = exc_info.value.errors()
        assert any("response" in str(e["loc"]) for e in errors)

    def test_invalid_severity_rejected(self):
        """Invalid severity value is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CreateCaseRequest(
                email="user@example.com",
                issue="Something broke.",
                severity="urgent",
            )
        errors = exc_info.value.errors()
        assert any("severity" in str(e["loc"]) for e in errors)

    def test_case_id_field_excluded(self):
        """case_id is not accepted as a field on CreateCaseRequest."""
        req = CreateCaseRequest(
            email="user@example.com",
            issue="Something broke.",
            severity="low",
            case_id="550e8400-e29b-41d4-a716-446655440000",
        )
        # case_id should not appear in the model fields
        assert "case_id" not in req.model_fields


# ---------------------------------------------------------------------------
# UpdateCaseRequest tests
# ---------------------------------------------------------------------------


class TestUpdateCaseRequest:
    """Tests for UpdateCaseRequest model."""

    def test_valid_input_all_fields(self):
        """Valid input with all required fields is accepted."""
        req = UpdateCaseRequest(
            email="updated@example.com",
            issue="Updated issue description.",
            response="We fixed it.",
            severity="medium",
        )
        assert req.email == "updated@example.com"
        assert req.issue == "Updated issue description."
        assert req.response == "We fixed it."
        assert req.severity == "medium"

    def test_missing_email_raises_validation_error(self):
        """Missing email raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateCaseRequest(
                issue="Something broke.",
                response="Noted.",
                severity="low",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("email",) for e in errors)

    def test_missing_issue_raises_validation_error(self):
        """Missing issue raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateCaseRequest(
                email="user@example.com",
                response="Noted.",
                severity="low",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("issue",) for e in errors)

    def test_missing_response_raises_validation_error(self):
        """Missing response raises ValidationError (required in update)."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateCaseRequest(
                email="user@example.com",
                issue="Something broke.",
                severity="low",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("response",) for e in errors)

    def test_missing_severity_raises_validation_error(self):
        """Missing severity raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateCaseRequest(
                email="user@example.com",
                issue="Something broke.",
                response="Noted.",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("severity",) for e in errors)

    def test_email_exceeds_254_chars_rejected(self):
        """Email exceeding 254 characters is rejected."""
        long_email = "a" * 246 + "@test.com"  # 255 chars total
        with pytest.raises(ValidationError) as exc_info:
            UpdateCaseRequest(
                email=long_email,
                issue="Something broke.",
                response="Noted.",
                severity="low",
            )
        errors = exc_info.value.errors()
        assert any("email" in str(e["loc"]) for e in errors)

    def test_email_without_at_rejected(self):
        """Email without @ symbol is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateCaseRequest(
                email="userexample.com",
                issue="Something broke.",
                response="Noted.",
                severity="low",
            )
        errors = exc_info.value.errors()
        assert any("email" in str(e["loc"]) for e in errors)

    def test_issue_empty_string_rejected(self):
        """Empty issue string is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateCaseRequest(
                email="user@example.com",
                issue="",
                response="Noted.",
                severity="low",
            )
        errors = exc_info.value.errors()
        assert any("issue" in str(e["loc"]) for e in errors)

    def test_issue_exceeds_2000_chars_rejected(self):
        """Issue exceeding 2000 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateCaseRequest(
                email="user@example.com",
                issue="x" * 2001,
                response="Noted.",
                severity="low",
            )
        errors = exc_info.value.errors()
        assert any("issue" in str(e["loc"]) for e in errors)

    def test_response_exceeds_5000_chars_rejected(self):
        """Response exceeding 5000 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateCaseRequest(
                email="user@example.com",
                issue="Something broke.",
                response="r" * 5001,
                severity="low",
            )
        errors = exc_info.value.errors()
        assert any("response" in str(e["loc"]) for e in errors)

    def test_invalid_severity_rejected(self):
        """Invalid severity value is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateCaseRequest(
                email="user@example.com",
                issue="Something broke.",
                response="Noted.",
                severity="urgent",
            )
        errors = exc_info.value.errors()
        assert any("severity" in str(e["loc"]) for e in errors)

    def test_case_id_field_excluded(self):
        """case_id is not accepted as a field on UpdateCaseRequest."""
        req = UpdateCaseRequest(
            email="user@example.com",
            issue="Something broke.",
            response="Noted.",
            severity="low",
            case_id="550e8400-e29b-41d4-a716-446655440000",
        )
        assert "case_id" not in req.model_fields


# ---------------------------------------------------------------------------
# ErrorResponse tests
# ---------------------------------------------------------------------------


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    def test_valid_input(self):
        """Valid detail string is accepted."""
        err = ErrorResponse(detail="Case not found.")
        assert err.detail == "Case not found."

    def test_detail_exceeds_500_chars_rejected(self):
        """Detail exceeding 500 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ErrorResponse(detail="x" * 501)
        errors = exc_info.value.errors()
        assert any("detail" in str(e["loc"]) for e in errors)

    def test_missing_detail_raises_validation_error(self):
        """Missing detail field raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ErrorResponse()
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("detail",) for e in errors)

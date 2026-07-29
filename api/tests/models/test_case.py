import uuid

import pytest
from pydantic import ValidationError

from app.models.case import CaseModel

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_DATA = {
    "case_id": uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
    "email": "user@example.com",
    "issue": "The dashboard fails to load after login.",
    "response": "We have identified the issue and deployed a fix in v2.3.1.",
    "severity": "high",
}

EXPECTED_KEYS = {"case_id", "email", "issue", "response", "severity"}
REQUIRED_FIELDS = list(EXPECTED_KEYS)


# ---------------------------------------------------------------------------
# Requirement 2.6 — Successful construction with all valid field values
# ---------------------------------------------------------------------------

def test_construction_with_valid_fields():
    model = CaseModel(**VALID_DATA)
    assert model.case_id == VALID_DATA["case_id"]
    assert model.email == VALID_DATA["email"]
    assert model.issue == VALID_DATA["issue"]
    assert model.response == VALID_DATA["response"]
    assert model.severity == VALID_DATA["severity"]


# ---------------------------------------------------------------------------
# Requirement 3.1 — model_dump() keys and case_id type
# ---------------------------------------------------------------------------

def test_model_dump_returns_expected_keys():
    model = CaseModel(**VALID_DATA)
    dumped = model.model_dump()
    assert set(dumped.keys()) == EXPECTED_KEYS


def test_model_dump_case_id_is_uuid():
    model = CaseModel(**VALID_DATA)
    dumped = model.model_dump()
    assert isinstance(dumped["case_id"], uuid.UUID)


# ---------------------------------------------------------------------------
# Requirements 3.2, 3.4 — model_validate() round-trip
# ---------------------------------------------------------------------------

def test_model_validate_round_trip():
    original = CaseModel(**VALID_DATA)
    restored = CaseModel.model_validate(original.model_dump())
    assert restored.case_id == original.case_id
    assert restored.email == original.email
    assert restored.issue == original.issue
    assert restored.response == original.response
    assert restored.severity == original.severity


# ---------------------------------------------------------------------------
# Requirement 3.3 — model_validate() raises ValidationError for missing field
# ---------------------------------------------------------------------------

def test_model_validate_missing_required_field_raises():
    data = dict(VALID_DATA)
    data.pop("email")  # remove one required field
    with pytest.raises(ValidationError):
        CaseModel.model_validate(data)


# ---------------------------------------------------------------------------
# Requirement 2.1 — Invalid UUID string raises ValidationError
# ---------------------------------------------------------------------------

def test_invalid_uuid_raises():
    data = dict(VALID_DATA)
    data["case_id"] = "not-a-uuid"
    with pytest.raises(ValidationError):
        CaseModel(**data)


# ---------------------------------------------------------------------------
# Requirement 2.2 — Empty string for email raises ValidationError
# ---------------------------------------------------------------------------

def test_empty_email_raises():
    data = dict(VALID_DATA)
    data["email"] = ""
    with pytest.raises(ValidationError):
        CaseModel(**data)


# ---------------------------------------------------------------------------
# Requirement 2.3 — Email without @ raises ValidationError
# ---------------------------------------------------------------------------

def test_email_without_at_raises():
    data = dict(VALID_DATA)
    data["email"] = "userexample.com"
    with pytest.raises(ValidationError):
        CaseModel(**data)


# ---------------------------------------------------------------------------
# Requirement 2.3 — Email with two @ characters raises ValidationError
# ---------------------------------------------------------------------------

def test_email_with_two_at_raises():
    data = dict(VALID_DATA)
    data["email"] = "user@@example.com"
    with pytest.raises(ValidationError):
        CaseModel(**data)


# ---------------------------------------------------------------------------
# Requirement 2.4 — Empty string for issue raises ValidationError
# ---------------------------------------------------------------------------

def test_empty_issue_raises():
    data = dict(VALID_DATA)
    data["issue"] = ""
    with pytest.raises(ValidationError):
        CaseModel(**data)


# ---------------------------------------------------------------------------
# Requirement 2.5 — Unknown severity value raises ValidationError
# ---------------------------------------------------------------------------

def test_unknown_severity_raises():
    data = dict(VALID_DATA)
    data["severity"] = "urgent"
    with pytest.raises(ValidationError):
        CaseModel(**data)


# ---------------------------------------------------------------------------
# Requirement 2.7 — None for any required field raises ValidationError
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_none_field_raises(field):
    data = dict(VALID_DATA)
    data[field] = None
    with pytest.raises(ValidationError):
        CaseModel(**data)


# ---------------------------------------------------------------------------
# Requirement 4.4 — model_json_schema() contains description and examples keys
# ---------------------------------------------------------------------------

def test_model_json_schema_contains_description_and_examples():
    schema = CaseModel.model_json_schema()
    properties = schema.get("properties", {})
    assert set(properties.keys()) == EXPECTED_KEYS, (
        f"Schema properties mismatch: {set(properties.keys())}"
    )
    for field_name, field_schema in properties.items():
        assert "description" in field_schema, (
            f"Field '{field_name}' is missing 'description' in schema"
        )
        has_examples = "examples" in field_schema or "example" in field_schema
        assert has_examples, (
            f"Field '{field_name}' is missing 'examples'/'example' in schema"
        )

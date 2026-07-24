# Feature: case-api, Property 7: Request model field constraint equivalence
"""Property-based tests for request model field constraint equivalence.

**Validates: Requirements 9.1, 9.2, 9.3**

Property 7: For any dictionary of field values, if the dictionary is accepted by
CaseModel (ignoring case_id), then it SHALL also be accepted by CreateCaseRequest
(with response defaulting) and UpdateCaseRequest — and vice versa: if rejected by
CaseModel for a shared field constraint, the request models SHALL also reject it.
"""

import uuid

from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from app.models.case import CaseModel
from app.models.requests import CreateCaseRequest, UpdateCaseRequest


# ---------------------------------------------------------------------------
# Strategies — generate a mix of valid and invalid field values
# ---------------------------------------------------------------------------

# Emails: mix of valid-ish and invalid values
email_strategy = st.one_of(
    # Valid emails
    st.from_regex(r"[a-z0-9]{1,64}@[a-z]{1,63}\.[a-z]{2,10}", fullmatch=True).filter(
        lambda e: len(e) <= 254
    ),
    # Too long
    st.just("a" * 250 + "@b.com"),
    # Missing @
    st.just("nope"),
    # Empty
    st.just(""),
)

# Issues: mix of valid and invalid lengths
issue_strategy = st.one_of(
    # Valid (1-2000 chars)
    st.text(min_size=1, max_size=2000, alphabet=st.characters(blacklist_categories=("Cs",))),
    # Empty (invalid)
    st.just(""),
    # Too long (invalid)
    st.text(min_size=2001, max_size=2050, alphabet=st.characters(blacklist_categories=("Cs",))),
)

# Responses: mix of valid and invalid lengths
response_strategy = st.one_of(
    # Valid (0-5000 chars)
    st.text(max_size=5000, alphabet=st.characters(blacklist_categories=("Cs",))),
    # Too long (invalid)
    st.text(min_size=5001, max_size=5050, alphabet=st.characters(blacklist_categories=("Cs",))),
)

# Severity: mix of valid and invalid values
severity_strategy = st.one_of(
    st.sampled_from(["low", "medium", "high", "critical"]),
    st.just("urgent"),  # invalid
    st.just(""),  # invalid
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _try_validate_case_model(fields: dict) -> bool:
    """Try to validate fields against CaseModel (with a dummy case_id).
    Returns True if accepted, False if rejected."""
    try:
        CaseModel(case_id=uuid.uuid4(), **fields)
        return True
    except (ValidationError, ValueError):
        return False


def _try_validate_create_request(fields: dict) -> bool:
    """Try to validate fields against CreateCaseRequest.
    Returns True if accepted, False if rejected."""
    try:
        CreateCaseRequest(**fields)
        return True
    except (ValidationError, ValueError):
        return False


def _try_validate_update_request(fields: dict) -> bool:
    """Try to validate fields against UpdateCaseRequest.
    Returns True if accepted, False if rejected."""
    try:
        UpdateCaseRequest(**fields)
        return True
    except (ValidationError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Property test
# ---------------------------------------------------------------------------


@given(
    email=email_strategy,
    issue=issue_strategy,
    response=response_strategy,
    severity=severity_strategy,
)
@settings(max_examples=100)
def test_request_model_field_constraint_equivalence(
    email: str, issue: str, response: str, severity: str
) -> None:
    """Property 7: Request model field constraint equivalence.

    For shared fields, CaseModel acceptance/rejection must agree with
    CreateCaseRequest and UpdateCaseRequest.
    """
    fields = {
        "email": email,
        "issue": issue,
        "response": response,
        "severity": severity,
    }

    case_model_accepts = _try_validate_case_model(fields)

    # UpdateCaseRequest has the same required fields as CaseModel (minus case_id)
    update_accepts = _try_validate_update_request(fields)

    # CreateCaseRequest is the same but response defaults to "" if not provided.
    # Since we ARE providing response explicitly, it should behave equivalently.
    create_accepts = _try_validate_create_request(fields)

    # Assertion: acceptance/rejection must agree across all three models
    assert case_model_accepts == update_accepts, (
        f"CaseModel {'accepted' if case_model_accepts else 'rejected'} but "
        f"UpdateCaseRequest {'accepted' if update_accepts else 'rejected'} "
        f"for fields: {fields}"
    )
    assert case_model_accepts == create_accepts, (
        f"CaseModel {'accepted' if case_model_accepts else 'rejected'} but "
        f"CreateCaseRequest {'accepted' if create_accepts else 'rejected'} "
        f"for fields: {fields}"
    )

"""Property-based tests for InMemoryCaseDAL.

Uses Hypothesis to validate the six correctness properties defined in the
design document for the Case Data Access Layer.
"""

import uuid

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.dal import InMemoryCaseDAL
from app.models.case import CaseModel


# ---------------------------------------------------------------------------
# Reusable strategies
# ---------------------------------------------------------------------------

valid_severity = st.sampled_from(["low", "medium", "high", "critical"])

valid_email = st.from_regex(
    r"[a-z0-9]{1,64}@[a-z]{1,63}\.[a-z]{2,10}", fullmatch=True
).filter(lambda e: len(e) <= 254)

valid_uuid = st.uuids()

valid_case_dict = st.fixed_dictionaries(
    {
        "case_id": valid_uuid,
        "email": valid_email,
        "issue": st.text(min_size=1, max_size=2000),
        "response": st.text(max_size=5000),
        "severity": valid_severity,
    }
)


@st.composite
def valid_case_model(draw: st.DrawFn) -> CaseModel:
    """Strategy that builds a valid CaseModel instance."""
    data = draw(valid_case_dict)
    return CaseModel(**data)


@st.composite
def distinct_case_models(draw: st.DrawFn, min_size: int = 1, max_size: int = 10) -> list[CaseModel]:
    """Strategy that generates a list of CaseModel instances with distinct case_id values."""
    n = draw(st.integers(min_value=min_size, max_value=max_size))
    cases: list[CaseModel] = []
    seen_ids: set[uuid.UUID] = set()
    for _ in range(n):
        case = draw(valid_case_model())
        assume(case.case_id not in seen_ids)
        seen_ids.add(case.case_id)
        cases.append(case)
    return cases


# ---------------------------------------------------------------------------
# Property 1: Create-then-retrieve round-trip
# ---------------------------------------------------------------------------

# Feature: case-dal, Property 1: Create-then-retrieve round-trip
@given(case=valid_case_model())
@settings(max_examples=100)
def test_create_then_retrieve_round_trip(case: CaseModel) -> None:
    """For any valid CaseModel, create_case followed by get_case_by_id returns
    an identical model with all fields equal.

    **Validates: Requirements 2.1, 2.3, 6.1, 6.4**
    """
    dal = InMemoryCaseDAL()
    created = dal.create_case(case)
    retrieved = dal.get_case_by_id(case.case_id)

    assert created == case
    assert retrieved == case
    assert retrieved.case_id == case.case_id
    assert retrieved.email == case.email
    assert retrieved.issue == case.issue
    assert retrieved.response == case.response
    assert retrieved.severity == case.severity


# ---------------------------------------------------------------------------
# Property 2: Duplicate create rejection preserves store
# ---------------------------------------------------------------------------

# Feature: case-dal, Property 2: Duplicate create rejection preserves store
@given(case=valid_case_model())
@settings(max_examples=100)
def test_duplicate_create_rejection_preserves_store(case: CaseModel) -> None:
    """Creating a case that already exists raises ValueError and the original
    case remains unchanged in the store.

    **Validates: Requirements 2.2**
    """
    dal = InMemoryCaseDAL()
    dal.create_case(case)

    # Attempt to create again with same case_id
    duplicate = CaseModel(
        case_id=case.case_id,
        email="duplicate@test.com",
        issue="duplicate issue",
        response="duplicate response",
        severity="low",
    )

    with pytest.raises(ValueError):
        dal.create_case(duplicate)

    # Original case is still intact
    stored = dal.get_case_by_id(case.case_id)
    assert stored == case


# ---------------------------------------------------------------------------
# Property 3: Update replaces stored value
# ---------------------------------------------------------------------------

# Feature: case-dal, Property 3: Update replaces stored value
@given(original=valid_case_model(), replacement=valid_case_model())
@settings(max_examples=100)
def test_update_replaces_stored_value(original: CaseModel, replacement: CaseModel) -> None:
    """Updating an existing case replaces the stored value entirely. The
    return value of update_case and subsequent get_case_by_id both match
    the replacement.

    **Validates: Requirements 3.1, 3.3**
    """
    dal = InMemoryCaseDAL()
    dal.create_case(original)

    updated = dal.update_case(original.case_id, replacement)
    retrieved = dal.get_case_by_id(original.case_id)

    assert updated == replacement
    assert retrieved == replacement


# ---------------------------------------------------------------------------
# Property 4: Delete removes case from store
# ---------------------------------------------------------------------------

# Feature: case-dal, Property 4: Delete removes case from store
@given(cases=distinct_case_models(min_size=2, max_size=10))
@settings(max_examples=100)
def test_delete_removes_case_from_store(cases: list[CaseModel]) -> None:
    """Deleting an existing case decreases get_all_cases length by one and
    causes get_case_by_id to raise KeyError for the deleted case_id.

    **Validates: Requirements 4.1, 4.3, 4.5**
    """
    dal = InMemoryCaseDAL()
    for case in cases:
        dal.create_case(case)

    target = cases[0]
    count_before = len(dal.get_all_cases())

    dal.delete_case(target.case_id)

    count_after = len(dal.get_all_cases())
    assert count_after == count_before - 1

    with pytest.raises(KeyError):
        dal.get_case_by_id(target.case_id)


# ---------------------------------------------------------------------------
# Property 5: Non-existent ID operations raise KeyError
# ---------------------------------------------------------------------------

# Feature: case-dal, Property 5: Non-existent ID operations raise KeyError
@given(case=valid_case_model(), missing_id=valid_uuid)
@settings(max_examples=100)
def test_non_existent_id_operations_raise_key_error(case: CaseModel, missing_id: uuid.UUID) -> None:
    """For any UUID not present in the store, get_case_by_id, update_case,
    and delete_case all raise KeyError.

    **Validates: Requirements 1.9, 1.10, 3.2, 4.2, 6.2**
    """
    dal = InMemoryCaseDAL()
    dal.create_case(case)

    # Ensure missing_id is actually not in the store
    assume(missing_id != case.case_id)

    with pytest.raises(KeyError):
        dal.get_case_by_id(missing_id)

    with pytest.raises(KeyError):
        dal.update_case(missing_id, case)

    with pytest.raises(KeyError):
        dal.delete_case(missing_id)


# ---------------------------------------------------------------------------
# Property 6: get_all_cases count invariant
# ---------------------------------------------------------------------------

# Feature: case-dal, Property 6: get_all_cases count invariant
@given(cases=distinct_case_models(min_size=0, max_size=15))
@settings(max_examples=100)
def test_get_all_cases_count_invariant(cases: list[CaseModel]) -> None:
    """After creating n cases with distinct case_id values (no deletions),
    get_all_cases returns exactly n items and every created case appears
    in the result.

    **Validates: Requirements 5.1, 5.3**
    """
    dal = InMemoryCaseDAL()
    for case in cases:
        dal.create_case(case)

    all_cases = dal.get_all_cases()
    assert len(all_cases) == len(cases)

    # Every created case is present in the result
    all_case_ids = {c.case_id for c in all_cases}
    for case in cases:
        assert case.case_id in all_case_ids

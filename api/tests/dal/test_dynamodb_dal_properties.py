"""Property-based tests for DynamoDBCaseDAL.

Uses Hypothesis with moto to validate the correctness properties defined in the
design document for the DynamoDB Data Access Layer.
"""

import os
import uuid

import boto3
import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from moto import mock_aws

from app.models.case import CaseModel


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TABLE_NAME = "test-project-cases"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_table() -> None:
    """Create the moto DynamoDB table used by the DAL."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[{"AttributeName": "case_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "case_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )


def _create_dal():
    """Create a DynamoDBCaseDAL instance pointing at the moto table."""
    os.environ["DYNAMODB_TABLE_NAME"] = TABLE_NAME
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"

    from aws_dal.dynamodb_case_dal import DynamoDBCaseDAL

    return DynamoDBCaseDAL()


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


# Feature: dynamodb-backend, Property 1: Create-then-retrieve round-trip
@given(case=valid_case_model())
@settings(max_examples=100, deadline=None)
def test_create_then_retrieve_round_trip(case: CaseModel) -> None:
    """For any valid CaseModel, create_case followed by get_case_by_id returns
    an identical model with all fields equal.

    **Validates: Requirements 3.8, 3.9**
    """
    with mock_aws():
        _setup_table()
        dal = _create_dal()

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
# Property 4: Pagination returns complete results
# ---------------------------------------------------------------------------

# Feature: dynamodb-backend, Property 4: Pagination returns complete results
@given(cases=distinct_case_models(min_size=1, max_size=15))
@settings(max_examples=100, deadline=None)
def test_pagination_returns_complete_results(cases: list[CaseModel]) -> None:
    """For any set of N distinct CaseModel instances stored in the table,
    get_all_cases returns exactly N items and every stored case appears.

    **Validates: Requirements 3.11**
    """
    with mock_aws():
        _setup_table()
        dal = _create_dal()

        for case in cases:
            dal.create_case(case)

        all_cases = dal.get_all_cases()
        assert len(all_cases) == len(cases)

        # Every created case is present in the result
        all_case_ids = {c.case_id for c in all_cases}
        for case in cases:
            assert case.case_id in all_case_ids


# ---------------------------------------------------------------------------
# Property 3: Non-existent ID operations raise KeyError
# ---------------------------------------------------------------------------

# Feature: dynamodb-backend, Property 3: Non-existent ID operations raise KeyError
@given(case=valid_case_model(), missing_id=st.uuids())
@settings(max_examples=100, deadline=None)
def test_non_existent_id_operations_raise_key_error(case: CaseModel, missing_id: uuid.UUID) -> None:
    """For any UUID not present in the store, get_case_by_id, update_case,
    and delete_case all raise KeyError.

    Validates: Requirements 3.4, 3.5, 3.6
    """
    with mock_aws():
        _setup_table()
        dal = _create_dal()
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
# Property 2: Duplicate create rejection preserves store
# ---------------------------------------------------------------------------

# Feature: dynamodb-backend, Property 2: Duplicate create rejection preserves store
@given(case=valid_case_model())
@settings(max_examples=100, deadline=None)
def test_duplicate_create_rejection_preserves_store(case: CaseModel) -> None:
    """Creating a case that already exists raises ValueError and the original
    case remains unchanged in the store.

    **Validates: Requirements 3.3**
    """
    with mock_aws():
        _setup_table()
        dal = _create_dal()

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

# Feature: case-api, Property 1: Create-then-retrieve round-trip
# Feature: case-api, Property 4: Update-then-retrieve round-trip
# Feature: case-api, Property 3: Get-all completeness invariant
"""Property-based tests for the cases router.

Uses Hypothesis to verify universal correctness properties of the API endpoints.
"""

from hypothesis import given, settings
from hypothesis import strategies as st
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_dal
from app.dal.in_memory_case_dal import InMemoryCaseDAL


SEVERITIES = ["low", "medium", "high", "critical"]


def valid_email_strategy():
    """Generate valid email addresses matching ^[^@]+@[^@]+$ with max 254 chars."""
    local = st.text(
        alphabet=st.characters(blacklist_characters="@", blacklist_categories=("Cs",)),
        min_size=1,
        max_size=64,
    )
    domain = st.text(
        alphabet=st.characters(blacklist_characters="@", blacklist_categories=("Cs",)),
        min_size=1,
        max_size=64,
    )
    return st.builds(lambda l, d: f"{l}@{d}", local, domain).filter(
        lambda e: len(e) <= 254
    )


def valid_issue_strategy():
    """Generate valid issue strings (1-2000 chars)."""
    return st.text(min_size=1, max_size=2000).filter(lambda s: s.strip() != "" or len(s) >= 1)


def valid_response_strategy():
    """Generate valid response strings (0-5000 chars)."""
    return st.text(min_size=0, max_size=5000)


def valid_create_request_strategy():
    """Generate valid CreateCaseRequest dicts."""
    return st.fixed_dictionaries({
        "email": valid_email_strategy(),
        "issue": valid_issue_strategy(),
        "response": valid_response_strategy(),
        "severity": st.sampled_from(SEVERITIES),
    })


def valid_update_request_strategy():
    """Generate valid UpdateCaseRequest dicts."""
    return st.fixed_dictionaries({
        "email": valid_email_strategy(),
        "issue": valid_issue_strategy(),
        "response": valid_response_strategy(),
        "severity": st.sampled_from(SEVERITIES),
    })


# ---------- Property 1: Create-then-retrieve round-trip ----------
# **Validates: Requirements 3.1, 5.1**


@settings(max_examples=100)
@given(body=valid_create_request_strategy())
def test_create_then_retrieve_round_trip(body):
    """For any valid CreateCaseRequest, POSTing it to /cases and then GETting
    /cases/{case_id} using the returned case_id SHALL produce a response whose
    email, issue, response, and severity fields are identical to the original request.

    **Validates: Requirements 3.1, 5.1**
    """
    # Fresh DAL per test example to ensure isolation
    dal = InMemoryCaseDAL()
    app.dependency_overrides[get_dal] = lambda: dal
    try:
        client = TestClient(app)

        # Step 1: POST to create
        create_resp = client.post("/cases", json=body)
        assert create_resp.status_code == 201, (
            f"Expected 201, got {create_resp.status_code}: {create_resp.text}"
        )
        created = create_resp.json()
        case_id = created["case_id"]

        # Step 2: GET by returned case_id
        get_resp = client.get(f"/cases/{case_id}")
        assert get_resp.status_code == 200, (
            f"Expected 200, got {get_resp.status_code}: {get_resp.text}"
        )
        retrieved = get_resp.json()

        # Step 3: Assert field equality
        assert retrieved["email"] == body["email"]
        assert retrieved["issue"] == body["issue"]
        assert retrieved["response"] == body["response"]
        assert retrieved["severity"] == body["severity"]
        assert retrieved["case_id"] == case_id
    finally:
        app.dependency_overrides.clear()


# ---------- Property 4: Update-then-retrieve round-trip ----------
# **Validates: Requirements 6.1**


@settings(max_examples=100)
@given(
    create_body=valid_create_request_strategy(),
    update_body=valid_update_request_strategy(),
)
def test_update_then_retrieve_round_trip(create_body, update_body):
    """For any existing case and any valid UpdateCaseRequest, PUTting to /cases/{case_id}
    and then GETting /cases/{case_id} SHALL produce a response whose email, issue,
    response, and severity match the update request body.

    **Validates: Requirements 6.1**
    """
    # Fresh DAL per test example to ensure isolation
    dal = InMemoryCaseDAL()
    app.dependency_overrides[get_dal] = lambda: dal
    try:
        client = TestClient(app)

        # Step 1: POST the create request to get a case_id
        create_resp = client.post("/cases", json=create_body)
        assert create_resp.status_code == 201, f"Create failed: {create_resp.text}"
        case_id = create_resp.json()["case_id"]

        # Step 2: PUT the update request to /cases/{case_id}
        update_resp = client.put(f"/cases/{case_id}", json=update_body)
        assert update_resp.status_code == 200, f"Update failed: {update_resp.text}"

        # Step 3: GET /cases/{case_id}
        get_resp = client.get(f"/cases/{case_id}")
        assert get_resp.status_code == 200, f"Get failed: {get_resp.text}"

        # Step 4: Assert the GET response fields match the update request
        retrieved = get_resp.json()
        assert retrieved["email"] == update_body["email"]
        assert retrieved["issue"] == update_body["issue"]
        assert retrieved["response"] == update_body["response"]
        assert retrieved["severity"] == update_body["severity"]
        assert retrieved["case_id"] == case_id
    finally:
        app.dependency_overrides.clear()


# ---------- Property 5: Non-existent ID yields 404 ----------
# **Validates: Requirements 5.2, 6.2, 7.2**


@settings(max_examples=100)
@given(case_id=st.uuids())
def test_non_existent_id_yields_404(case_id):
    """For any UUID that does not correspond to an existing case,
    GET /cases/{uuid}, PUT /cases/{uuid}, and DELETE /cases/{uuid} SHALL all
    return HTTP 404 with an ErrorResponse body containing the unrecognized
    case_id in the detail message.

    **Validates: Requirements 5.2, 6.2, 7.2**
    """
    # Override with a fresh empty DAL for each test invocation
    fresh_dal = InMemoryCaseDAL()
    app.dependency_overrides[get_dal] = lambda: fresh_dal
    try:
        client = TestClient(app)
        str_id = str(case_id)

        # GET /cases/{uuid} should return 404
        get_resp = client.get(f"/cases/{str_id}")
        assert get_resp.status_code == 404, (
            f"GET /cases/{str_id} returned {get_resp.status_code}, expected 404"
        )
        get_body = get_resp.json()
        assert "detail" in get_body
        assert str_id in get_body["detail"], (
            f"Expected case_id '{str_id}' in detail, got: {get_body['detail']}"
        )

        # PUT /cases/{uuid} with valid body should return 404
        valid_update_body = {
            "email": "user@example.com",
            "issue": "Test",
            "response": "",
            "severity": "low",
        }
        put_resp = client.put(f"/cases/{str_id}", json=valid_update_body)
        assert put_resp.status_code == 404, (
            f"PUT /cases/{str_id} returned {put_resp.status_code}, expected 404"
        )
        put_body = put_resp.json()
        assert "detail" in put_body
        assert str_id in put_body["detail"], (
            f"Expected case_id '{str_id}' in detail, got: {put_body['detail']}"
        )

        # DELETE /cases/{uuid} should return 404
        del_resp = client.delete(f"/cases/{str_id}")
        assert del_resp.status_code == 404, (
            f"DELETE /cases/{str_id} returned {del_resp.status_code}, expected 404"
        )
        del_body = del_resp.json()
        assert "detail" in del_body
        assert str_id in del_body["detail"], (
            f"Expected case_id '{str_id}' in detail, got: {del_body['detail']}"
        )
    finally:
        app.dependency_overrides.clear()


# ---------- Property 2: Validation rejection without DAL invocation ----------
# Feature: case-api, Property 2: Validation rejection without DAL invocation
# **Validates: Requirements 3.2, 6.3, 9.3, 9.5**

import uuid
from unittest.mock import MagicMock


# --- Strategies for generating invalid request bodies ---

VALID_SEVERITIES = ["low", "medium", "high", "critical"]


@st.composite
def invalid_email_too_long(draw):
    """Generate an email that exceeds the 254-character limit."""
    # @test.com is 9 chars, so local_length + 9 must be > 254
    # local_length must be >= 246 to make total >= 255
    local_length = draw(st.integers(min_value=246, max_value=500))
    local = "a" * local_length
    return f"{local}@test.com"


@st.composite
def invalid_issue_too_long(draw):
    """Generate an issue that exceeds the 2000-character limit."""
    length = draw(st.integers(min_value=2001, max_value=3000))
    return "x" * length


@st.composite
def invalid_response_too_long(draw):
    """Generate a response that exceeds the 5000-character limit."""
    length = draw(st.integers(min_value=5001, max_value=6000))
    return "r" * length


@st.composite
def invalid_severity(draw):
    """Generate a severity not in the allowed set."""
    bad = draw(
        st.text(min_size=1, max_size=20).filter(lambda s: s not in VALID_SEVERITIES)
    )
    return bad


@st.composite
def invalid_create_case_body(draw):
    """
    Generate a CreateCaseRequest body that violates at least one field constraint.
    Chooses one violation type at random and applies it.
    """
    violation = draw(st.sampled_from([
        "email_too_long",
        "issue_empty",
        "issue_too_long",
        "response_too_long",
        "bad_severity",
        "missing_email",
        "missing_issue",
        "missing_severity",
    ]))

    # Start with a valid base
    body = {
        "email": "valid@example.com",
        "issue": "A valid issue description",
        "response": "",
        "severity": "low",
    }

    if violation == "email_too_long":
        body["email"] = draw(invalid_email_too_long())
    elif violation == "issue_empty":
        body["issue"] = ""
    elif violation == "issue_too_long":
        body["issue"] = draw(invalid_issue_too_long())
    elif violation == "response_too_long":
        body["response"] = draw(invalid_response_too_long())
    elif violation == "bad_severity":
        body["severity"] = draw(invalid_severity())
    elif violation == "missing_email":
        del body["email"]
    elif violation == "missing_issue":
        del body["issue"]
    elif violation == "missing_severity":
        del body["severity"]

    return body


@st.composite
def invalid_update_case_body(draw):
    """
    Generate an UpdateCaseRequest body that violates at least one field constraint.
    Chooses one violation type at random and applies it.
    """
    violation = draw(st.sampled_from([
        "email_too_long",
        "issue_empty",
        "issue_too_long",
        "response_too_long",
        "bad_severity",
        "missing_email",
        "missing_issue",
        "missing_response",
        "missing_severity",
    ]))

    # Start with a valid base
    body = {
        "email": "valid@example.com",
        "issue": "A valid issue description",
        "response": "A valid response",
        "severity": "medium",
    }

    if violation == "email_too_long":
        body["email"] = draw(invalid_email_too_long())
    elif violation == "issue_empty":
        body["issue"] = ""
    elif violation == "issue_too_long":
        body["issue"] = draw(invalid_issue_too_long())
    elif violation == "response_too_long":
        body["response"] = draw(invalid_response_too_long())
    elif violation == "bad_severity":
        body["severity"] = draw(invalid_severity())
    elif violation == "missing_email":
        del body["email"]
    elif violation == "missing_issue":
        del body["issue"]
    elif violation == "missing_response":
        del body["response"]
    elif violation == "missing_severity":
        del body["severity"]

    return body


class TestValidationRejectionWithoutDALInvocation:
    """
    Property 2: For any request body that violates the field constraints of
    CreateCaseRequest or UpdateCaseRequest (email exceeds 254 chars, issue empty
    or exceeds 2000 chars, response exceeds 5000 chars, severity not in allowed
    set, or missing required fields), the API SHALL return HTTP 422 and the DAL
    SHALL NOT be invoked.

    **Validates: Requirements 3.2, 6.3, 9.3, 9.5**
    """

    @given(body=invalid_create_case_body())
    @settings(max_examples=100)
    def test_post_invalid_body_returns_422_and_dal_not_called(self, body):
        """POST /cases with invalid body returns 422, DAL never called."""
        mock_dal = MagicMock()
        app.dependency_overrides[get_dal] = lambda: mock_dal

        try:
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/cases", json=body)

            assert response.status_code == 422, (
                f"Expected 422 but got {response.status_code} for body: {body}"
            )
            mock_dal.create_case.assert_not_called()
        finally:
            app.dependency_overrides.clear()

    @given(body=invalid_update_case_body())
    @settings(max_examples=100)
    def test_put_invalid_body_returns_422_and_dal_not_called(self, body):
        """PUT /cases/{uuid} with invalid body returns 422, DAL never called."""
        mock_dal = MagicMock()
        app.dependency_overrides[get_dal] = lambda: mock_dal

        try:
            client = TestClient(app, raise_server_exceptions=False)
            case_id = str(uuid.uuid4())
            response = client.put(f"/cases/{case_id}", json=body)

            assert response.status_code == 422, (
                f"Expected 422 but got {response.status_code} for body: {body}"
            )
            mock_dal.update_case.assert_not_called()
        finally:
            app.dependency_overrides.clear()


# ---------- Property 3: Get-all completeness invariant ----------
# **Validates: Requirements 4.1, 4.2**


@settings(max_examples=100, deadline=None)
@given(cases=st.lists(valid_create_request_strategy(), min_size=1, max_size=10))
def test_get_all_completeness_invariant(cases):
    """For any sequence of N create operations (each with distinct case_id, no
    deletions), GET /cases SHALL return exactly N items, and the set of case_ids
    in the response SHALL equal the set of case_ids generated during creation.

    **Validates: Requirements 4.1, 4.2**
    """
    # Fresh DAL per test example to ensure isolation
    dal = InMemoryCaseDAL()
    app.dependency_overrides[get_dal] = lambda: dal
    try:
        client = TestClient(app)
        created_case_ids = set()

        # POST all cases
        for case_body in cases:
            resp = client.post("/cases", json=case_body)
            assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
            created_case_ids.add(resp.json()["case_id"])

        # GET /cases
        get_resp = client.get("/cases")
        assert get_resp.status_code == 200

        returned_cases = get_resp.json()
        returned_case_ids = {c["case_id"] for c in returned_cases}

        # Assert count matches
        assert len(returned_cases) == len(cases), (
            f"Expected {len(cases)} cases, got {len(returned_cases)}"
        )

        # Assert case_id sets match
        assert returned_case_ids == created_case_ids, (
            f"Case ID mismatch.\n"
            f"  Created: {created_case_ids}\n"
            f"  Returned: {returned_case_ids}"
        )
    finally:
        app.dependency_overrides.clear()


# ---------- Property 6: Delete-then-retrieve yields 404 ----------
# Feature: case-api, Property 6: Delete-then-retrieve yields 404
# **Validates: Requirements 7.1, 7.5**


@settings(max_examples=100)
@given(body=valid_create_request_strategy())
def test_delete_then_retrieve_yields_404(body):
    """For any case that has been successfully created and then deleted (receiving
    HTTP 204), a subsequent GET /cases/{case_id} SHALL return HTTP 404 and
    GET /cases SHALL NOT include that case_id.

    **Validates: Requirements 7.1, 7.5**
    """
    # Fresh DAL per test example to ensure isolation
    dal = InMemoryCaseDAL()
    app.dependency_overrides[get_dal] = lambda: dal
    try:
        client = TestClient(app)

        # Step 1: POST to create a case
        create_resp = client.post("/cases", json=body)
        assert create_resp.status_code == 201, (
            f"Expected 201, got {create_resp.status_code}: {create_resp.text}"
        )
        case_id = create_resp.json()["case_id"]

        # Step 2: DELETE /cases/{case_id} — assert 204
        delete_resp = client.delete(f"/cases/{case_id}")
        assert delete_resp.status_code == 204, (
            f"Expected 204, got {delete_resp.status_code}: {delete_resp.text}"
        )

        # Step 3: GET /cases/{case_id} — assert 404
        get_resp = client.get(f"/cases/{case_id}")
        assert get_resp.status_code == 404, (
            f"Expected 404 after delete, got {get_resp.status_code}: {get_resp.text}"
        )

        # Step 4: GET /cases — assert case_id not in the returned list
        list_resp = client.get("/cases")
        assert list_resp.status_code == 200
        returned_ids = [c["case_id"] for c in list_resp.json()]
        assert case_id not in returned_ids, (
            f"Deleted case_id {case_id} should not appear in GET /cases response"
        )
    finally:
        app.dependency_overrides.clear()


# ---------- Property 8: Error sanitization ----------
# Feature: case-api, Property 8: Error sanitization
# **Validates: Requirements 10.3**


# Strategy: Generate random exception messages that simulate sensitive info
@st.composite
def sensitive_exception_message(draw):
    """Generate exception messages containing sensitive-looking info
    (file paths, variable names, stack traces)."""
    sensitive_patterns = [
        # File paths
        lambda d: f"Error reading {d(st.sampled_from(['/etc/passwd', '/home/user/.env', 'C:\\\\Users\\\\admin\\\\secrets.txt', '/var/lib/db/data.sqlite']))}",
        # Variable names and internal details
        lambda d: f"NameError: name '{d(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('L',))))}' is not defined",
        # Stack trace fragments
        lambda d: f"Traceback (most recent call last):\n  File \"{d(st.sampled_from(['/app/dal/case_dal.py', '/usr/lib/python3.11/site-packages/sqlalchemy/engine.py']))}\", line {d(st.integers(min_value=1, max_value=999))}, in {d(st.sampled_from(['connect', 'execute', '_process_query']))}",
        # Connection strings
        lambda d: f"Could not connect to {d(st.sampled_from(['postgresql://admin:password123@db.internal:5432/cases', 'redis://secret@cache.local:6379', 'mongodb://root:toor@mongo.internal/admin']))}",
        # Generic sensitive messages
        lambda d: f"Failed to authenticate with token={d(st.text(min_size=10, max_size=40, alphabet=st.characters(whitelist_categories=('Nd', 'L'))))}",
    ]
    pattern_fn = draw(st.sampled_from(sensitive_patterns))
    return pattern_fn(draw)


# Unexpected exception types that should trigger 500 (not KeyError, ValueError, TypeError)
UNEXPECTED_EXCEPTION_TYPES = [RuntimeError, OSError, IOError, ConnectionError, PermissionError, TimeoutError]


# DAL methods that can be triggered by various endpoints
DAL_METHODS_AND_ENDPOINTS = [
    ("create_case", "POST", "/cases", {"email": "user@test.com", "issue": "Test issue", "response": "", "severity": "low"}),
    ("get_all_cases", "GET", "/cases", None),
    ("get_case_by_id", "GET", "/cases/00000000-0000-0000-0000-000000000001", None),
    ("update_case", "PUT", "/cases/00000000-0000-0000-0000-000000000001", {"email": "user@test.com", "issue": "Test issue", "response": "resp", "severity": "low"}),
    ("delete_case", "DELETE", "/cases/00000000-0000-0000-0000-000000000001", None),
]


@settings(max_examples=100)
@given(
    exc_message=sensitive_exception_message(),
    exc_type_idx=st.integers(min_value=0, max_value=len(UNEXPECTED_EXCEPTION_TYPES) - 1),
    endpoint_idx=st.integers(min_value=0, max_value=len(DAL_METHODS_AND_ENDPOINTS) - 1),
)
def test_error_sanitization(exc_message, exc_type_idx, endpoint_idx):
    """For any unexpected exception type raised by the DAL (i.e., not KeyError,
    ValueError, or TypeError), the API SHALL return HTTP 500 with an ErrorResponse
    whose detail field is a fixed generic message and does NOT contain stack traces,
    file paths, or variable names from the exception.

    **Validates: Requirements 10.3**
    """
    exc_type = UNEXPECTED_EXCEPTION_TYPES[exc_type_idx]
    dal_method, http_method, path, body = DAL_METHODS_AND_ENDPOINTS[endpoint_idx]

    # Create a mock DAL that raises the unexpected exception on the target method
    mock_dal = MagicMock()
    getattr(mock_dal, dal_method).side_effect = exc_type(exc_message)

    app.dependency_overrides[get_dal] = lambda: mock_dal
    try:
        client = TestClient(app, raise_server_exceptions=False)

        # Make the request
        if http_method == "POST":
            response = client.post(path, json=body)
        elif http_method == "GET":
            response = client.get(path)
        elif http_method == "PUT":
            response = client.put(path, json=body)
        elif http_method == "DELETE":
            response = client.delete(path)

        # Assert 500 status code
        assert response.status_code == 500, (
            f"Expected 500 but got {response.status_code} for {exc_type.__name__}('{exc_message}') "
            f"on {http_method} {path}"
        )

        # Assert response body has the fixed generic message
        resp_body = response.json()
        assert resp_body["detail"] == "An internal error occurred", (
            f"Expected fixed generic message, got: {resp_body['detail']}"
        )

        # Assert the sensitive exception message does NOT appear in the response body
        response_text = response.text
        assert exc_message not in response_text, (
            f"Sensitive exception message leaked into response: {exc_message}"
        )
    finally:
        app.dependency_overrides.clear()


# ---------- Property 9: Error responses use JSON content-type ----------
# Feature: case-api, Property 9: Error responses use JSON content-type
# **Validates: Requirements 10.6**


@st.composite
def error_trigger_strategy(draw):
    """
    Generate scenarios that trigger various HTTP error responses (404, 400, 422, 500).
    Returns a tuple of (method, path, json_body, error_type_description).
    """
    error_type = draw(st.sampled_from([
        "404_get",
        "404_put",
        "404_delete",
        "422_post_invalid_body",
        "422_put_invalid_body",
        "422_invalid_uuid",
        "400_value_error",
        "500_unexpected_exception",
    ]))

    random_uuid = str(draw(st.uuids()))

    if error_type == "404_get":
        return ("GET", f"/cases/{random_uuid}", None, "404_get")
    elif error_type == "404_put":
        valid_body = {
            "email": "test@example.com",
            "issue": "Test issue",
            "response": "",
            "severity": "low",
        }
        return ("PUT", f"/cases/{random_uuid}", valid_body, "404_put")
    elif error_type == "404_delete":
        return ("DELETE", f"/cases/{random_uuid}", None, "404_delete")
    elif error_type == "422_post_invalid_body":
        # Missing required fields or invalid values
        invalid_body = draw(st.sampled_from([
            {},
            {"email": "bad"},
            {"email": "a" * 300 + "@test.com", "issue": "x", "severity": "low"},
            {"email": "x@y.com", "issue": "", "severity": "low"},
            {"email": "x@y.com", "issue": "ok", "severity": "invalid_sev"},
        ]))
        return ("POST", "/cases", invalid_body, "422_post")
    elif error_type == "422_put_invalid_body":
        invalid_body = draw(st.sampled_from([
            {},
            {"email": "bad"},
            {"email": "x@y.com", "issue": "", "response": "", "severity": "low"},
            {"email": "x@y.com", "issue": "ok", "response": "", "severity": "nope"},
        ]))
        return ("PUT", f"/cases/{random_uuid}", invalid_body, "422_put")
    elif error_type == "422_invalid_uuid":
        method = draw(st.sampled_from(["GET", "PUT", "DELETE"]))
        path = "/cases/not-a-valid-uuid"
        body = None
        if method == "PUT":
            body = {
                "email": "x@y.com",
                "issue": "ok",
                "response": "",
                "severity": "low",
            }
        return (method, path, body, "422_invalid_uuid")
    elif error_type == "400_value_error":
        return ("GET", f"/cases/{random_uuid}", None, "400_value_error")
    elif error_type == "500_unexpected_exception":
        return ("GET", f"/cases/{random_uuid}", None, "500_unexpected")

    # Fallback (shouldn't reach here)
    return ("GET", f"/cases/{random_uuid}", None, "404_get")


@settings(max_examples=100)
@given(trigger=error_trigger_strategy())
def test_error_responses_use_json_content_type(trigger):
    """For any API request that results in an HTTP 4xx or 5xx response,
    the response Content-Type header SHALL be application/json.

    **Validates: Requirements 10.6**
    """
    method, path, body, error_type = trigger

    # For 400 and 500 triggers, we need to mock the DAL
    if error_type == "400_value_error":
        mock_dal = MagicMock()
        mock_dal.get_case_by_id.side_effect = ValueError("invalid value")
        mock_dal.get_all_cases.side_effect = ValueError("invalid value")
        app.dependency_overrides[get_dal] = lambda: mock_dal
    elif error_type == "500_unexpected":
        mock_dal = MagicMock()
        mock_dal.get_case_by_id.side_effect = RuntimeError("unexpected crash")
        mock_dal.get_all_cases.side_effect = RuntimeError("unexpected crash")
        mock_dal.create_case.side_effect = RuntimeError("unexpected crash")
        mock_dal.update_case.side_effect = RuntimeError("unexpected crash")
        mock_dal.delete_case.side_effect = RuntimeError("unexpected crash")
        app.dependency_overrides[get_dal] = lambda: mock_dal
    else:
        # Use a fresh empty DAL for 404s, and no override needed for 422s
        # (FastAPI handles validation before DAL is called)
        fresh_dal = InMemoryCaseDAL()
        app.dependency_overrides[get_dal] = lambda: fresh_dal

    try:
        client = TestClient(app, raise_server_exceptions=False)

        if method == "GET":
            response = client.get(path)
        elif method == "POST":
            response = client.post(path, json=body)
        elif method == "PUT":
            response = client.put(path, json=body)
        elif method == "DELETE":
            response = client.delete(path)
        else:
            raise ValueError(f"Unexpected method: {method}")

        # Only check error responses (4xx and 5xx)
        if response.status_code >= 400:
            content_type = response.headers.get("content-type", "")
            assert "application/json" in content_type, (
                f"{method} {path} returned status {response.status_code} "
                f"with Content-Type '{content_type}', expected 'application/json'"
            )
    finally:
        app.dependency_overrides.clear()

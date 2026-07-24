# Implementation Plan: Case API

## Overview

Implement the Case API — a FastAPI application exposing CRUD endpoints for support cases, with pluggable DAL selection via IoC/dependency injection. The existing `CaseModel`, `CaseDAL`, and `InMemoryCaseDAL` are already in place; this plan adds configuration, dependency wiring, request/error models, route handlers, and comprehensive tests.

## Tasks

- [x] 1. Set up dependencies and configuration
  - [x] 1.1 Update requirements.txt with FastAPI ecosystem packages
    - Add `fastapi==0.115.0`, `pydantic==2.9.2`, `pydantic-settings==2.5.2`, `uvicorn==0.30.6`, `httpx==0.27.2`, `pytest==8.3.3` to `requirements.txt`
    - Ensure `hypothesis==6.112.2` remains
    - _Requirements: Design dependencies section_

  - [x] 1.2 Create app/config.py with AppSettings
    - Implement `AppSettings(BaseSettings)` class with `dal_implementation: str` defaulting to `"InMemoryCaseDAL"`
    - Implement `get_settings()` factory function
    - _Requirements: 2.1, 2.2_

  - [x] 1.3 Create app/dependencies.py with DAL registry and get_dal provider
    - Define `DAL_REGISTRY: dict[str, Type[CaseDAL]]` mapping `"InMemoryCaseDAL"` to `InMemoryCaseDAL`
    - Implement `get_dal()` function that reads settings, looks up the registry, and returns an instance
    - Raise `ValueError` if the configured DAL name is not in the registry
    - _Requirements: 2.1, 2.3, 2.4, 2.5_

- [x] 2. Create request and error models
  - [x] 2.1 Create app/models/requests.py with CreateCaseRequest and UpdateCaseRequest
    - `CreateCaseRequest`: fields `email`, `issue`, `severity` (required), `response` (optional, default empty string); excludes `case_id`
    - `UpdateCaseRequest`: fields `email`, `issue`, `response`, `severity` (all required); excludes `case_id`
    - Field constraints must mirror CaseModel: email max 254 chars with pattern `^[^@]+@[^@]+$`, issue 1–2000 chars, response max 5000 chars, severity literal enum
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 2.2 Create app/models/errors.py with ErrorResponse model
    - Single field `detail: str` with `max_length=500`
    - _Requirements: 10.5_

  - [x] 2.3 Write property test for request model constraint equivalence
    - **Property 7: Request model field constraint equivalence**
    - **Validates: Requirements 9.1, 9.2, 9.3**
    - Create `tests/models/test_request_models_properties.py`
    - Generate field dicts and validate against CaseModel vs CreateCaseRequest/UpdateCaseRequest, asserting acceptance/rejection agreement

  - [x] 2.4 Write unit tests for request and error models
    - Create `tests/models/test_request_models.py`
    - Test valid inputs, boundary values, missing fields, constraint violations
    - _Requirements: 9.1, 9.2, 9.3, 9.5, 10.5_

- [x] 3. Implement router and application entry point
  - [x] 3.1 Create app/routers/__init__.py
    - Empty package marker file
    - _Requirements: 1.2_

  - [x] 3.2 Create app/routers/cases.py with all CRUD endpoint handlers
    - `POST /` → create_case: generate UUID4, build CaseModel, persist via DAL, return 201
    - `GET /` → get_all_cases: return list from DAL, 200
    - `GET /{case_id}` → get_case_by_id: return single case, 200
    - `PUT /{case_id}` → update_case: build CaseModel from path ID + body, persist, return 200
    - `DELETE /{case_id}` → delete_case: remove via DAL, return 204
    - Each handler must have `summary` and `description` in decorator
    - Each handler must declare `response_model` for success and error status codes
    - Each handler wraps DAL calls in try/except: KeyError→404, ValueError→400, TypeError→422, other→500
    - Use `Depends(get_dal)` for DAL injection
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2, 9.4, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

  - [x] 3.3 Create app/main.py with FastAPI instance and router registration
    - Create `FastAPI` app with title and version
    - Register cases router under `/cases` prefix with `tags=["cases"]`
    - Add root `GET /` endpoint returning `{"status": "ok"}`
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 4. Checkpoint - Ensure core application starts
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Write unit tests for configuration and application bootstrap
  - [x] 5.1 Create tests/test_config.py
    - Test default `dal_implementation` is `"InMemoryCaseDAL"`
    - Test invalid DAL name raises `ValueError` in `get_dal()`
    - Test custom DAL registration works when added to registry
    - _Requirements: 2.1, 2.2, 2.5_

  - [x] 5.2 Create tests/test_main.py
    - Test app instance exists
    - Test `GET /` returns 200 with `{"status": "ok"}`
    - Test `/docs`, `/redoc`, `/openapi.json` return 200
    - Test cases router is registered (POST/GET/PUT/DELETE on `/cases` are routable)
    - _Requirements: 1.1, 1.2, 1.3, 8.3, 8.4, 8.5_

- [x] 6. Write unit tests for router endpoints
  - [x] 6.1 Create tests/routers/__init__.py
    - Empty package marker
    - _Requirements: test structure_

  - [x] 6.2 Create tests/routers/test_cases.py with example-based endpoint tests
    - Test POST /cases with valid body returns 201 with generated case_id
    - Test POST /cases with invalid body returns 422
    - Test GET /cases returns 200 with list
    - Test GET /cases returns empty list when no cases exist
    - Test GET /cases/{id} returns 200 for existing case
    - Test GET /cases/{id} returns 404 for non-existent case
    - Test GET /cases/{id} returns 422 for invalid UUID
    - Test PUT /cases/{id} returns 200 for valid update
    - Test PUT /cases/{id} returns 404 for non-existent case
    - Test PUT /cases/{id} returns 422 for invalid body
    - Test DELETE /cases/{id} returns 204 for existing case
    - Test DELETE /cases/{id} returns 404 for non-existent case
    - Test error responses have Content-Type application/json
    - Test DAL ValueError → 400, TypeError → 422, unexpected exception → 500 with fixed message
    - _Requirements: 3.1, 3.2, 3.4, 4.1, 4.2, 4.4, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 6.5, 7.1, 7.2, 7.4, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [x] 7. Checkpoint - Ensure all unit tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Write property-based tests for router endpoints
  - [x] 8.1 Write property test for create-then-retrieve round-trip
    - **Property 1: Create-then-retrieve round-trip**
    - **Validates: Requirements 3.1, 5.1**
    - Create `tests/routers/test_cases_properties.py`
    - Generate valid CreateCaseRequest dicts via Hypothesis, POST, then GET by returned case_id, assert field equality

  - [x] 8.2 Write property test for validation rejection without DAL invocation
    - **Property 2: Validation rejection without DAL invocation**
    - **Validates: Requirements 3.2, 6.3, 9.3, 9.5**
    - Generate invalid field values (email too long, issue empty/too long, response too long, bad severity), POST/PUT, assert 422

  - [x] 8.3 Write property test for get-all completeness invariant
    - **Property 3: Get-all completeness invariant**
    - **Validates: Requirements 4.1, 4.2**
    - Generate N valid cases, POST all, GET /cases, assert count and case_id set match

  - [x] 8.4 Write property test for update-then-retrieve round-trip
    - **Property 4: Update-then-retrieve round-trip**
    - **Validates: Requirements 6.1**
    - Create case, generate valid update body, PUT, then GET and compare fields

  - [x] 8.5 Write property test for non-existent ID yields 404
    - **Property 5: Non-existent ID yields 404**
    - **Validates: Requirements 5.2, 6.2, 7.2**
    - Generate random UUIDs, attempt GET/PUT/DELETE on empty app, assert 404

  - [x] 8.6 Write property test for delete-then-retrieve yields 404
    - **Property 6: Delete-then-retrieve yields 404**
    - **Validates: Requirements 7.1, 7.5**
    - Create case, DELETE (assert 204), then GET same ID (assert 404), GET /cases (assert not in list)

  - [x] 8.7 Write property test for error sanitization
    - **Property 8: Error sanitization**
    - **Validates: Requirements 10.3**
    - Mock DAL to raise RuntimeError/OSError with sensitive info, assert 500 response detail is fixed generic message

  - [x] 8.8 Write property test for error responses use JSON content-type
    - **Property 9: Error responses use JSON content-type**
    - **Validates: Requirements 10.6**
    - Trigger various errors (404, 400, 422, 500), assert Content-Type header is `application/json`

- [x] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The existing `CaseModel`, `CaseDAL`, and `InMemoryCaseDAL` are already implemented and tested — this plan builds on top of them
- Use `fastapi.testclient.TestClient` for all HTTP-level tests (synchronous, no server needed)
- Use `unittest.mock.patch` to mock DAL dependencies where needed for error simulation

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "2.1", "2.2", "3.1"] },
    { "id": 1, "tasks": ["1.3", "2.3", "2.4"] },
    { "id": 2, "tasks": ["3.2", "3.3"] },
    { "id": 3, "tasks": ["5.1", "5.2", "6.1"] },
    { "id": 4, "tasks": ["6.2"] },
    { "id": 5, "tasks": ["8.1", "8.2", "8.3", "8.4", "8.5", "8.6", "8.7", "8.8"] }
  ]
}
```

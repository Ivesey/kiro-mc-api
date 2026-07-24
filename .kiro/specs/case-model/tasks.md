# Implementation Plan: CaseModel

## Overview

Implement the `CaseModel` Pydantic model in `app/models/case.py`, add the `hypothesis` dependency to `requirements.txt`, and write unit and property-based tests under `tests/models/`.

## Tasks

- [x] 1. Add hypothesis dependency to requirements.txt
  - Append `hypothesis==6.112.2` to `requirements.txt` with an exact pinned version
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

- [x] 2. Implement CaseModel
  - [x] 2.1 Create `app/models/case.py` with the `CaseModel` class
    - Import `uuid`, `Literal` from `typing`, `BaseModel` and `Field` from `pydantic`
    - Define `CaseModel(BaseModel)` with five fields: `case_id`, `email`, `issue`, `response`, `severity`
    - `case_id`: type `uuid.UUID`, `Field(...)` with `description` and `examples`
    - `email`: type `str`, `Field(..., max_length=254, pattern=r"^[^@]+@[^@]+$")` with `description` and `examples`
    - `issue`: type `str`, `Field(..., min_length=1, max_length=2000)` with `description` and `examples`
    - `response`: type `str`, `Field(..., max_length=5000)` with `description` and `examples`
    - `severity`: type `Literal["low", "medium", "high", "critical"]`, `Field(...)` with `description` and `examples`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 4.1, 4.2, 4.3_

- [x] 3. Write unit tests for CaseModel
  - [x] 3.1 Create `tests/models/test_case.py`
    - Add `tests/models/__init__.py` if it does not exist
    - Test successful construction with all valid field values (Requirements 2.6)
    - Test `model_dump()` returns a dict with exactly the 5 expected keys and `case_id` as `uuid.UUID` (Requirements 3.1)
    - Test `model_validate()` round-trip: validate a dumped instance reconstructs with equal field values (Requirements 3.2, 3.4)
    - Test `model_validate()` raises `ValidationError` for a dict missing a required field (Requirements 3.3)
    - Test invalid UUID string raises `ValidationError` (Requirements 2.1)
    - Test empty string for `email` raises `ValidationError` (Requirements 2.2)
    - Test email without `@` raises `ValidationError` (Requirements 2.3)
    - Test email with two `@` characters raises `ValidationError` (Requirements 2.3)
    - Test empty string for `issue` raises `ValidationError` (Requirements 2.4)
    - Test unknown `severity` value raises `ValidationError` (Requirements 2.5)
    - Test `None` for any required field raises `ValidationError` (Requirements 2.7)
    - Test `model_json_schema()` contains `"description"` and `"examples"` keys for each of the 5 fields (Requirements 4.4)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 3.1, 3.2, 3.3, 3.4, 4.4_

- [x] 4. Checkpoint — Ensure all unit tests pass
  - Run `venv\Scripts\pytest tests/models/test_case.py`
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Write property-based tests for CaseModel
  - [x] 5.1 Create `tests/models/test_case_properties.py`
    - Import `hypothesis`, `given`, `settings`, `strategies as st`, and `assume`
    - Define reusable strategies: `valid_severity`, `valid_email`, `valid_uuid`, `valid_case_dict`
    - _Requirements: 2.6, 3.4_

  - [ ]* 5.2 Write property test for Property 1: Round-trip serialization
    - **Property 1: Round-trip serialization**
    - `@given(valid_case_dict)` — construct a `CaseModel`, call `model_dump()`, call `model_validate()` on the result, assert each field is equal to the original
    - **Validates: Requirements 3.1, 3.4**

  - [ ]* 5.3 Write property test for Property 2: Valid construction succeeds for all valid inputs
    - **Property 2: Valid construction succeeds for all valid inputs**
    - `@given(valid_case_dict)` — assert `CaseModel(**data)` does not raise
    - **Validates: Requirements 2.6**

  - [ ]* 5.4 Write property test for Property 3: Invalid UUID is rejected
    - **Property 3: Invalid UUID is rejected**
    - `@given(st.text().filter(lambda s: not _is_valid_uuid(s)))` — assert `ValidationError` is raised
    - **Validates: Requirements 2.1**

  - [ ]* 5.5 Write property test for Property 4: Invalid email format is rejected
    - **Property 4: Invalid email format is rejected**
    - `@given(st.text().filter(lambda s: s.count("@") != 1 or s.startswith("@") or s.endswith("@")))` — assert `ValidationError` is raised
    - **Validates: Requirements 2.2, 2.3**

  - [ ]* 5.6 Write property test for Property 5: Field length constraints are enforced
    - **Property 5: Field length constraints are enforced**
    - Over-limit email (`st.text(min_size=255, max_size=300).filter(lambda s: "@" not in s)` appended with `@x.com`) → assert `ValidationError`
    - Over-limit issue (`st.text(min_size=2001, max_size=2100)`) → assert `ValidationError`
    - Over-limit response (`st.text(min_size=5001, max_size=5100)`) → assert `ValidationError`
    - **Validates: Requirements 1.3, 1.4, 1.5**

  - [ ]* 5.7 Write property test for Property 6: Invalid severity is rejected
    - **Property 6: Invalid severity is rejected**
    - `@given(st.text().filter(lambda s: s not in {"low", "medium", "high", "critical"}))` — assert `ValidationError` is raised
    - **Validates: Requirements 2.5**

  - [ ]* 5.8 Write property test for Property 7: None or absent required field is rejected
    - **Property 7: None or absent required field is rejected**
    - `@given(valid_case_dict, st.sampled_from(["case_id", "email", "issue", "response", "severity"]))` — set chosen field to `None`, assert `ValidationError`
    - **Validates: Requirements 2.7**

  - [ ]* 5.9 Write property test for Property 8: Schema metadata completeness
    - **Property 8: Schema metadata completeness**
    - Iterate over `CaseModel.model_fields.items()` — assert each field has a non-empty `description` and at least one `example` that satisfies the field's own validation constraints
    - **Validates: Requirements 4.2, 4.3, 4.4**

- [x] 6. Final checkpoint — Ensure all tests pass
  - Run `venv\Scripts\pytest tests/models/`
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Property tests must each include a comment referencing the design property number: `# Feature: case-model, Property N: <title>`
- Run tests with `venv\Scripts\pytest tests/models/` — never use watch mode
- `hypothesis==6.112.2` must be pinned in `requirements.txt` before running property tests

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1", "2.1"] },
    { "id": 1, "tasks": ["3.1", "5.1"] },
    { "id": 2, "tasks": ["5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "5.8", "5.9"] }
  ]
}
```

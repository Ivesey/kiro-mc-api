# Implementation Plan: Case Data Access Layer (CaseDAL)

## Overview

Implement the abstract base class `CaseDAL` and the in-memory concrete implementation `InMemoryCaseDAL` in `app/dal/`, along with comprehensive unit and property-based tests. The implementation follows a layered architecture where routers depend on the DAL abstraction, enabling testability and future backend swaps.

## Tasks

- [x] 1. Set up DAL module structure and abstract base class
  - [x] 1.1 Create `app/dal/__init__.py` and `app/dal/case_dal.py` with the `CaseDAL` abstract base class
    - Create `app/dal/` directory with `__init__.py`
    - Define `CaseDAL` as an `abc.ABC` subclass in `app/dal/case_dal.py`
    - Declare all five abstract methods: `create_case`, `update_case`, `delete_case`, `get_all_cases`, `get_case_by_id`
    - Include full type annotations and docstrings with error contracts
    - Export `CaseDAL` from `app/dal/__init__.py`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 7.1, 7.2, 7.3, 7.4_

- [x] 2. Implement InMemoryCaseDAL concrete class
  - [x] 2.1 Implement `InMemoryCaseDAL` in `app/dal/case_dal.py`
    - Create `InMemoryCaseDAL` subclass with `dict[uuid.UUID, CaseModel]` internal store
    - Implement `create_case`: persist case, raise `ValueError` on duplicate `case_id`
    - Implement `update_case`: validate inputs, raise `ValueError` for None/invalid `case_id` or None case, raise `KeyError` if not found, replace stored case
    - Implement `delete_case`: validate `case_id`, raise `ValueError` for None/invalid, raise `KeyError` if not found, remove from store
    - Implement `get_all_cases`: return list of all stored `CaseModel` instances
    - Implement `get_case_by_id`: validate `case_id` type (raise `TypeError` for None/non-UUID), raise `KeyError` if not found, return stored case
    - Export `InMemoryCaseDAL` from `app/dal/__init__.py`
    - _Requirements: 1.8, 1.9, 1.10, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 6.4_

- [x] 3. Write unit tests for CaseDAL
  - [x] 3.1 Create `tests/dal/__init__.py` and `tests/dal/test_case_dal.py` with unit tests
    - Create `tests/dal/` directory with `__init__.py`
    - Test ABC enforcement: incomplete subclass raises `TypeError` on instantiation
    - Test empty store: `get_all_cases` returns `[]`
    - Test `create_case` persists and returns matching `CaseModel`
    - Test `create_case` raises `ValueError` on duplicate `case_id`
    - Test `update_case` replaces stored case and returns updated model
    - Test `update_case` raises `KeyError` for non-existent `case_id`
    - Test `update_case` raises `ValueError` when `case_id` is `None`
    - Test `update_case` raises `ValueError` when `case` is `None`
    - Test `delete_case` removes case from store
    - Test `delete_case` raises `KeyError` for non-existent `case_id`
    - Test `delete_case` raises `ValueError` when `case_id` is `None`
    - Test `get_case_by_id` returns correct case
    - Test `get_case_by_id` raises `KeyError` for non-existent `case_id`
    - Test `get_case_by_id` raises `TypeError` when `case_id` is `None`
    - Test `get_case_by_id` raises `TypeError` when `case_id` is non-UUID type
    - Test module exports: `from app.dal import CaseDAL, InMemoryCaseDAL` succeeds
    - Test no router/HTTP imports in `case_dal.py`
    - _Requirements: 1.1, 1.7, 1.8, 1.9, 1.10, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 6.1, 6.2, 6.3, 6.4, 7.2, 7.3_

- [x] 4. Checkpoint - Ensure all unit tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Write property-based tests for CaseDAL
  - [x] 5.1 Write property test for create-then-retrieve round-trip
    - **Property 1: Create-then-retrieve round-trip**
    - Create a valid `CaseModel`, call `create_case`, then `get_case_by_id` with the same `case_id`; assert all fields are equal
    - **Validates: Requirements 2.1, 2.3, 6.1, 6.4**

  - [x] 5.2 Write property test for duplicate create rejection
    - **Property 2: Duplicate create rejection preserves store**
    - Create a case, then attempt `create_case` again with the same `case_id`; assert `ValueError` is raised and original case remains unchanged
    - **Validates: Requirements 2.2**

  - [x] 5.3 Write property test for update replaces stored value
    - **Property 3: Update replaces stored value**
    - Create a case, call `update_case` with a new `CaseModel`, then `get_case_by_id`; assert fields match the replacement
    - **Validates: Requirements 3.1, 3.3**

  - [x] 5.4 Write property test for delete removes case from store
    - **Property 4: Delete removes case from store**
    - Create cases, delete one; assert `get_all_cases` length decreases by one and `get_case_by_id` raises `KeyError`
    - **Validates: Requirements 4.1, 4.3, 4.5**

  - [x] 5.5 Write property test for non-existent ID operations
    - **Property 5: Non-existent ID operations raise KeyError**
    - Generate a UUID not in the store; assert `get_case_by_id`, `update_case`, and `delete_case` all raise `KeyError`
    - **Validates: Requirements 1.9, 1.10, 3.2, 4.2, 6.2**

  - [x] 5.6 Write property test for get_all_cases count invariant
    - **Property 6: get_all_cases count invariant**
    - Create `n` cases with distinct `case_id` values (no deletions); assert `get_all_cases` returns exactly `n` items and all created cases appear
    - **Validates: Requirements 5.1, 5.3**

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using Hypothesis
- Unit tests validate specific examples, edge cases, and structural checks
- The existing `valid_case_dict` strategy in `tests/models/test_case_properties.py` can be reused/adapted for DAL property tests

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["3.1"] },
    { "id": 3, "tasks": ["5.1", "5.2", "5.3", "5.4", "5.5", "5.6"] }
  ]
}
```

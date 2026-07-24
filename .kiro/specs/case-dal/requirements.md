# Requirements Document

## Introduction

The Case Data Access Layer (DAL) feature introduces an abstract base class and the surrounding module structure that isolates all database interaction for support cases. Routers and other application layers call the DAL interface exclusively — they never query the database directly. The DAL exposes five operations: create a case, update a case, delete a case, retrieve all cases, and retrieve a single case by its identifier. Concrete implementations (e.g., in-memory, DynamoDB, PostgreSQL) will subclass the abstract base class and provide the actual persistence logic.

## Glossary

- **CaseDAL**: The abstract base class defining the contract for all case data access operations.
- **CaseModel**: The Pydantic model (`app.models.case.CaseModel`) that represents a support case/ticket entity.
- **case_id**: A `uuid.UUID` that uniquely identifies a single support case.
- **Concrete Implementation**: A subclass of `CaseDAL` that provides real database interaction (e.g., in-memory dict, DynamoDB table).
- **DAL**: Data Access Layer — the module (`app/dal/`) responsible for all database interaction; routers never query the database directly.
- **Router**: A FastAPI route handler module in `app/routers/` that depends on a `CaseDAL` instance injected via FastAPI's dependency injection.
- **Not Found**: The state where no case with the given `case_id` exists in the underlying store.

## Requirements

### Requirement 1: Abstract Base Class Interface

**User Story:** As a backend developer, I want an abstract base class that declares all DAL methods for case management, so that every concrete implementation is forced to fulfil the same contract and routers can depend on a stable interface.

#### Acceptance Criteria

1. THE CaseDAL SHALL be an abstract base class defined in `app/dal/case_dal.py` using `abc.ABC` and `abc.abstractmethod`.
2. THE CaseDAL SHALL declare an abstract method `create_case` that accepts a `CaseModel` instance and returns `CaseModel`.
3. THE CaseDAL SHALL declare an abstract method `update_case` that accepts a `case_id` of type `uuid.UUID` and a `CaseModel` instance, and returns `CaseModel`.
4. THE CaseDAL SHALL declare an abstract method `delete_case` that accepts a `case_id` of type `uuid.UUID` and returns `None`.
5. THE CaseDAL SHALL declare an abstract method `get_all_cases` that accepts no domain arguments and returns a `list[CaseModel]`.
6. THE CaseDAL SHALL declare an abstract method `get_case_by_id` that accepts a `case_id` of type `uuid.UUID` and returns `CaseModel`.
7. THE `app/dal/__init__.py` module SHALL export `CaseDAL` so that it is importable as `from app.dal import CaseDAL`.
8. IF a concrete subclass of `CaseDAL` does not implement all abstract methods, THEN attempting to instantiate that subclass SHALL raise a `TypeError`.
9. WHEN `get_case_by_id` is called with a `case_id` that does not exist in the store, THE CaseDAL SHALL raise a `KeyError` identifying the missing `case_id`.
10. WHEN `update_case` is called with a `case_id` that does not exist in the store, THE CaseDAL SHALL raise a `KeyError` identifying the missing `case_id`.

---

### Requirement 2: Create Case

**User Story:** As a backend developer, I want a `create_case` method on the DAL, so that a new support case can be persisted through a single, consistent interface.

#### Acceptance Criteria

1. WHEN `create_case` is called with a `CaseModel` instance, THE CaseDAL SHALL persist the case to the store and return a `CaseModel` instance.
2. IF the store already contains a record with the same `case_id` as the input `CaseModel`, THEN THE CaseDAL SHALL raise a `ValueError` with a message that includes the duplicate `case_id` value, and the existing record SHALL remain unchanged in the store.
3. WHEN `create_case` returns a `CaseModel` instance, THE returned `CaseModel` SHALL have every field value equal to the corresponding field value of the input `CaseModel`.

---

### Requirement 3: Update Case

**User Story:** As a backend developer, I want an `update_case` method on the DAL, so that existing support case data can be modified through a single, consistent interface.

#### Acceptance Criteria

1. WHEN `update_case` is called with a `case_id` that exists in the store and a valid `CaseModel` instance, THE CaseDAL SHALL replace the stored case with the provided `CaseModel` and return a `CaseModel` instance representing the updated record.
2. WHEN `update_case` is called with a `case_id` that does not exist in the store, THE CaseDAL SHALL raise a `KeyError` identifying the missing `case_id` and leave the store unchanged.
3. THE returned `CaseModel` from `update_case` SHALL have field values equal to the provided `CaseModel` argument's field values.
4. IF `update_case` is called with a `case_id` that is `None`, empty, or not a valid `uuid.UUID`, THEN THE CaseDAL SHALL raise a `ValueError` indicating the invalid `case_id`.
5. IF `update_case` is called with a `CaseModel` argument that is `None`, THEN THE CaseDAL SHALL raise a `ValueError` indicating the missing case data.

---

### Requirement 4: Delete Case

**User Story:** As a backend developer, I want a `delete_case` method on the DAL, so that a support case can be removed through a single, consistent interface.

#### Acceptance Criteria

1. WHEN `delete_case` is called with a `case_id` that exists in the store, THE CaseDAL SHALL remove the case from the store and return `None`.
2. WHEN `delete_case` is called with a `case_id` that does not exist in the store, THE CaseDAL SHALL raise a `KeyError` identifying the missing `case_id`.
3. WHEN `delete_case` is called with a `case_id` that exists in the store, THE CaseDAL SHALL ensure that a subsequent call to `get_case_by_id` with the same `case_id` raises a `KeyError`.
4. IF `delete_case` is called with a `case_id` that is `None` or not a valid `uuid.UUID`, THEN THE CaseDAL SHALL raise a `ValueError` indicating the invalid `case_id`.
5. WHEN `delete_case` successfully removes a case, THE total number of cases returned by `get_all_cases` SHALL decrease by exactly one.

---

### Requirement 5: Get All Cases

**User Story:** As a backend developer, I want a `get_all_cases` method on the DAL, so that the full list of support cases can be retrieved through a single, consistent interface.

#### Acceptance Criteria

1. WHEN `get_all_cases` is called and the store contains one or more cases, THE CaseDAL SHALL return a `list[CaseModel]` where each element is a valid `CaseModel` instance representing a stored case.
2. WHEN `get_all_cases` is called and the store is empty, THE CaseDAL SHALL return an empty `list`.
3. THE length of the list returned by `get_all_cases` SHALL equal the number of cases currently in the store.
4. IF the underlying store raises an exception during retrieval, THE CaseDAL SHALL propagate that exception without returning a partial result.

---

### Requirement 6: Get Case by ID

**User Story:** As a backend developer, I want a `get_case_by_id` method on the DAL, so that a single support case can be retrieved by its unique identifier through a consistent interface.

#### Acceptance Criteria

1. WHEN `get_case_by_id` is called with a `case_id` that exists in the store, THE CaseDAL SHALL return the `CaseModel` whose `case_id` field equals the provided `case_id`.
2. WHEN `get_case_by_id` is called with a `case_id` that does not exist in the store, THE CaseDAL SHALL raise a `KeyError` whose argument equals the provided `case_id`.
3. IF `get_case_by_id` is called with a `case_id` that is `None` or not a valid `uuid.UUID`, THEN THE CaseDAL SHALL raise a `TypeError` indicating the invalid argument type.
4. FOR ALL cases stored via `create_case`, calling `get_case_by_id` with the same `case_id` SHALL return a `CaseModel` with every field value exactly equal to those of the stored case, with no fields added, removed, or mutated (round-trip property).

---

### Requirement 7: Module Structure and Discoverability

**User Story:** As a backend developer, I want the DAL to follow the project's module layout, so that it is easy to locate, import, and extend without altering the router or model layers.

#### Acceptance Criteria

1. THE DAL module SHALL reside at `app/dal/` and SHALL contain at minimum `__init__.py` and `case_dal.py`.
2. THE `app/dal/__init__.py` file SHALL expose `CaseDAL` such that it is importable via `from app.dal import CaseDAL` without importing any submodule directly.
3. THE CaseDAL abstract base class SHALL NOT import from `app/routers/` or reference any HTTP framework constructs (e.g., FastAPI `Request`, `Response`, or status codes).
4. THE CaseDAL abstract base class SHALL only depend on the Python standard library and `app/models/case.CaseModel`.

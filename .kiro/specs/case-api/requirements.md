# Requirements Document

## Introduction

This document specifies the requirements for the Case API — a RESTful HTTP interface built with FastAPI that exposes support case CRUD operations. The API delegates all data access to a pluggable Data Access Layer (DAL) resolved at runtime through Inversion of Control (IoC), allowing the concrete DAL implementation to be swapped without modifying application code. The default implementation uses the existing InMemoryCaseDAL.

## Glossary

- **Case_API**: The FastAPI application exposing HTTP endpoints for support case management.
- **Router**: A FastAPI APIRouter grouping related endpoints under a common resource prefix.
- **DAL**: Data Access Layer — the abstract interface through which the API accesses case data.
- **InMemoryCaseDAL**: A concrete DAL implementation that stores cases in an in-memory dictionary.
- **IoC_Container**: The dependency injection mechanism (FastAPI's `Depends` system combined with application configuration) that resolves which concrete DAL implementation is used at runtime.
- **CaseModel**: The Pydantic model representing a complete support case entity.
- **CreateCaseRequest**: A Pydantic model representing the request body for creating a new case (excludes case_id).
- **UpdateCaseRequest**: A Pydantic model representing the request body for updating an existing case.
- **ErrorResponse**: A structured JSON error body returned when an operation fails.

## Requirements

### Requirement 1: Application Bootstrap and Router Registration

**User Story:** As a developer, I want a single FastAPI application entry point that registers all routers, so that the API is served from one unified app instance.

#### Acceptance Criteria

1. THE Case_API SHALL expose a FastAPI application instance in `app/main.py`.
2. THE Case_API SHALL register the cases Router under the `/cases` path prefix.
3. WHEN a GET request is sent to the root path `/`, THE Case_API SHALL return an HTTP 200 response with a JSON body containing a `"status"` key set to `"ok"`.

### Requirement 2: Dependency Injection for DAL Selection

**User Story:** As a developer, I want the concrete DAL class to be selected via configuration, so that I can swap implementations without changing application code.

#### Acceptance Criteria

1. THE IoC_Container SHALL resolve the concrete CaseDAL subclass by matching a string identifier from the `dal_implementation` setting in `app/config.py` to a registered DAL class name.
2. IF the `dal_implementation` setting is absent, empty, or not defined in the environment, THEN THE IoC_Container SHALL default to InMemoryCaseDAL.
3. WHEN a new DAL implementation is added and registered with the IoC_Container, THE IoC_Container SHALL instantiate and inject that implementation into route handlers when its string identifier is set as the `dal_implementation` configuration value, without modifying router or endpoint code.
4. THE Case_API SHALL use FastAPI's `Depends` mechanism to inject the resolved CaseDAL instance into route handlers.
5. IF the `dal_implementation` configuration value does not match any registered DAL class name, THEN THE IoC_Container SHALL raise an error at application startup indicating the unrecognized value.

### Requirement 3: Create Case Endpoint

**User Story:** As an API consumer, I want to create a new support case via HTTP POST, so that I can submit issues into the system.

#### Acceptance Criteria

1. WHEN a valid CreateCaseRequest is received at `POST /cases`, THE Case_API SHALL generate a UUID4 for the case_id, persist the resulting CaseModel via the DAL, and return HTTP 201 with the CaseModel in the response body containing the generated case_id and all submitted fields.
2. IF the CreateCaseRequest fails Pydantic validation, THEN THE Case_API SHALL return HTTP 422 with a JSON response body containing a list of validation errors, where each error identifies the field name and the reason for rejection.
3. THE Case_API SHALL document the POST /cases endpoint with a non-empty summary and a non-empty description in its OpenAPI schema.
4. IF the DAL raises a ValueError during case creation, THEN THE Case_API SHALL return HTTP 500 with a JSON response body containing an error message indicating an internal failure, without exposing internal details.

### Requirement 4: Get All Cases Endpoint

**User Story:** As an API consumer, I want to retrieve all support cases, so that I can display a list of existing tickets.

#### Acceptance Criteria

1. WHEN a GET request is received at `/cases`, THE Case_API SHALL return HTTP 200 with a JSON array of all CaseModel objects from the DAL, where each object contains the fields: case_id (UUID), email (string, max 254 characters), issue (string, 1–2000 characters), response (string, max 5000 characters), and severity (one of "low", "medium", "high", "critical").
2. WHEN the DAL contains no cases, THE Case_API SHALL return HTTP 200 with an empty JSON array (`[]`).
3. THE Case_API SHALL document the GET `/cases` endpoint with a summary and description in its OpenAPI schema.
4. IF the DAL raises an unhandled exception during retrieval, THEN THE Case_API SHALL return HTTP 500 with a JSON body containing an error message indicating an internal failure, without exposing internal details.

### Requirement 5: Get Case by ID Endpoint

**User Story:** As an API consumer, I want to retrieve a single support case by its ID, so that I can view the details of a specific ticket.

#### Acceptance Criteria

1. WHEN a GET request is received at `/cases/{case_id}` with a valid UUID path parameter, THE Case_API SHALL return HTTP 200 with a JSON body containing the matching CaseModel (fields: case_id, email, issue, response, severity).
2. IF no case with the given case_id exists, THEN THE Case_API SHALL return HTTP 404 with an ErrorResponse containing a message indicating which case_id was not found.
3. IF the case_id path parameter is not a valid UUID, THEN THE Case_API SHALL return HTTP 422 with an ErrorResponse containing a message indicating the value is not a valid UUID format.
4. THE Case_API SHALL document the GET /cases/{case_id} endpoint with a summary and description in its OpenAPI schema.

### Requirement 6: Update Case Endpoint

**User Story:** As an API consumer, I want to update an existing support case, so that I can modify case details such as the response or severity.

#### Acceptance Criteria

1. WHEN a valid UpdateCaseRequest is received at `PUT /cases/{case_id}` and the case_id corresponds to an existing case, THE Case_API SHALL construct a CaseModel using the path case_id and the request body fields, persist it via the DAL's update_case method, and return HTTP 200 with the full updated CaseModel as the response body.
2. IF no case with the given case_id exists in the DAL (KeyError raised), THEN THE Case_API SHALL return HTTP 404 with an ErrorResponse containing a message that identifies the case_id that was not found.
3. IF the UpdateCaseRequest fails Pydantic validation (e.g., email exceeds 254 characters, issue is empty or exceeds 2000 characters, response exceeds 5000 characters, or severity is not one of "low", "medium", "high", "critical"), THEN THE Case_API SHALL return HTTP 422 with an ErrorResponse indicating which field(s) failed validation.
4. IF the case_id path parameter is not a valid UUID format, THEN THE Case_API SHALL return HTTP 422 with an ErrorResponse indicating the invalid case_id format.
5. IF the DAL raises a ValueError during the update operation, THEN THE Case_API SHALL return HTTP 400 with an ErrorResponse indicating the invalid argument.
6. THE Case_API SHALL document the PUT /cases/{case_id} endpoint with a summary and description in its OpenAPI schema.

### Requirement 7: Delete Case Endpoint

**User Story:** As an API consumer, I want to delete a support case by ID, so that I can remove resolved or invalid tickets.

#### Acceptance Criteria

1. WHEN a DELETE request is received at `/cases/{case_id}` with a valid UUID that exists in the store, THE Case_API SHALL remove the case from the DAL and return HTTP 204 with no response body.
2. IF no case with the given case_id exists in the store, THEN THE Case_API SHALL return HTTP 404 with an ErrorResponse containing a message indicating that no case with the supplied case_id was found.
3. THE Case_API SHALL document the DELETE /cases/{case_id} endpoint with a summary and description in its OpenAPI schema.
4. IF the case_id path parameter is not a valid RFC 4122 UUID, THEN THE Case_API SHALL return HTTP 422 with a validation error response and SHALL NOT invoke the DAL.
5. WHEN a case has been successfully deleted, THE Case_API SHALL ensure the case is no longer retrievable via GET `/cases/{case_id}`, which SHALL return HTTP 404.

### Requirement 8: OpenAPI Documentation

**User Story:** As a developer, I want all API endpoints to be fully documented in the OpenAPI schema, so that consumers can discover and understand the API from the auto-generated docs.

#### Acceptance Criteria

1. THE Case_API SHALL include a non-empty summary (1–60 characters) and a non-empty description (1–300 characters) on every route handler decorator.
2. THE Case_API SHALL define Pydantic response models for all status codes each endpoint can return, including at minimum the success status code (200 or 201) and error status codes 404 and 422 where applicable.
3. WHEN a client sends a GET request to `/docs`, THE Case_API SHALL return an HTTP 200 response containing the Swagger UI HTML page that lists all registered endpoints.
4. WHEN a client sends a GET request to `/redoc`, THE Case_API SHALL return an HTTP 200 response containing the ReDoc HTML page that lists all registered endpoints.
5. WHEN a client sends a GET request to `/openapi.json`, THE Case_API SHALL return an HTTP 200 response with a valid OpenAPI 3.x JSON schema containing paths, summaries, descriptions, and response models for every registered endpoint.

### Requirement 9: Request and Response Models

**User Story:** As a developer, I want separate Pydantic models for request and response payloads, so that the API schema accurately represents what clients send versus what they receive.

#### Acceptance Criteria

1. THE CreateCaseRequest model SHALL include required fields email, issue, and severity, and an optional response field (defaulting to empty string) — and SHALL exclude case_id.
2. THE UpdateCaseRequest model SHALL include all fields (email, issue, response, and severity) as required, representing a full replacement of the case data, and SHALL exclude case_id.
3. THE CreateCaseRequest and UpdateCaseRequest models SHALL enforce the same field constraints as CaseModel for overlapping fields: email (max 254 characters, pattern ^[^@]+@[^@]+$), issue (1–2000 characters), response (max 5000 characters), and severity (one of "low", "medium", "high", "critical").
4. THE Case_API SHALL use CaseModel as the response model for endpoints that return a single case, and a list of CaseModel for endpoints that return multiple cases.
5. IF an incoming request body fails Pydantic validation, THEN THE Case_API SHALL return an HTTP 422 response with a body describing which fields failed validation, without invoking the DAL.

### Requirement 10: Error Handling

**User Story:** As an API consumer, I want consistent and descriptive error responses, so that I can programmatically handle failures.

#### Acceptance Criteria

1. WHEN a DAL operation raises a KeyError (case not found), THE Case_API SHALL return HTTP 404 with an ErrorResponse containing a "detail" field that describes which resource was not found.
2. WHEN a DAL operation raises a ValueError, THE Case_API SHALL return HTTP 400 with an ErrorResponse containing a "detail" field that describes the validation failure.
3. IF an unexpected exception occurs, THEN THE Case_API SHALL return HTTP 500 with an ErrorResponse whose "detail" field contains a fixed message and does not include stack traces, file paths, or variable names.
4. WHEN a DAL operation raises a TypeError (invalid argument type), THE Case_API SHALL return HTTP 422 with an ErrorResponse containing a "detail" field that describes the type mismatch.
5. THE Case_API SHALL represent all error responses using a Pydantic ErrorResponse model containing exactly one field: "detail" (string, maximum 500 characters).
6. IF the Case_API returns an error response (HTTP 4xx or 5xx), THEN THE Case_API SHALL set the response Content-Type header to "application/json".

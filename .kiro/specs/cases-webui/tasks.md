# Implementation Plan: Cases Web UI

## Overview

Build a lightweight, framework-free browser application in `webui/` that provides CRUD operations for support cases by consuming the existing FastAPI Cases REST API. The implementation uses plain HTML, CSS, and JavaScript split into focused modules. CORS must be enabled on the API to allow cross-origin requests from the Web UI. Property-based tests for pure validation functions use fast-check via Node.js.

## Tasks

- [x] 1. Enable CORS on the FastAPI backend
  - [x] 1.1 Add CORS middleware to `app/main.py`
    - Import `CORSMiddleware` from `fastapi.middleware.cors`
    - Add middleware allowing all origins, methods, and headers for development
    - Ensure the Cases API endpoints are accessible from browser-based JavaScript
    - _Requirements: 2.1, 2.3 (Web UI must be able to call the API from a different origin)_

- [x] 2. Create project structure and HTML entry point
  - [x] 2.1 Create `webui/index.html` with complete page structure
    - Create `webui/` directory at repository root
    - Build semantic HTML structure with: settings section (API URL input), case list section, create/edit form section, message/notification area
    - Include all `<script>` tags loading `js/validation.js`, `js/api.js`, `js/ui.js`, `js/app.js` in order
    - Include `<link>` to `styles.css`
    - Use proper `<label>`/`<input>` associations with `for`/`id` attributes
    - Use a `<select>` element for severity (constrains to low/medium/high/critical)
    - Add ARIA live regions for success/error announcements
    - Ensure all interactive elements are keyboard-accessible
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 4.1, 4.6, 5.2, 8.1, 8.2, 8.3, 8.5_

  - [x] 2.2 Create `webui/styles.css` with styling
    - Style the case list, forms, settings panel, and messages
    - Add severity badge colours (distinct for low, medium, high, critical)
    - Style loading indicators, disabled button states, focus indicators
    - Style inline validation error messages
    - Ensure focus indicators are visually distinct from default unfocused state
    - _Requirements: 3.3, 7.3, 8.4_

- [x] 3. Implement validation module
  - [x] 3.1 Create `webui/js/validation.js` with pure validation functions
    - Implement `validateApiUrl(url)` — returns `{valid, error?}`, accepts only `http://` or `https://` prefix and length <= 2048
    - Implement `validateEmail(email)` — returns `{valid, error?}`, requires exactly one `@` with non-empty local and domain parts
    - Implement `validateCaseForm(data)` — returns `{valid, errors}`, checks required fields (email, issue, severity), validates email format, validates severity is one of the four allowed values, checks issue length 1-2000, checks response length <= 5000
    - Implement `truncateText(text, maxLen)` — returns original if length <= maxLen, otherwise first maxLen chars + "..."
    - All functions are pure (no side effects, no DOM access) for testability
    - _Requirements: 2.1, 2.5, 3.2, 4.5, 4.7, 5.2_

  - [x] 3.2 Write property test for `validateApiUrl`
    - **Property 1: API URL validation correctness**
    - **Validates: Requirements 2.1, 2.5**
    - Use fast-check to generate arbitrary strings and valid http/https URLs of varying lengths
    - Verify accept/reject matches protocol prefix + length rules

  - [x] 3.3 Write property test for `validateEmail`
    - **Property 2: Email validation correctness**
    - **Validates: Requirements 4.7**
    - Use fast-check to generate strings with varying numbers of `@` characters
    - Verify classification matches the exactly-one-@ with non-empty-parts rule

  - [x] 3.4 Write property test for `truncateText`
    - **Property 3: Text truncation correctness**
    - **Validates: Requirements 3.2**
    - Use fast-check to generate strings of varying length and positive integer maxLen values
    - Verify short strings are returned unchanged and long strings are truncated to maxLen chars + "..."

  - [x] 3.5 Write property test for `validateCaseForm`
    - **Property 4: Form validation completeness**
    - **Validates: Requirements 4.5, 4.6, 5.2**
    - Use fast-check to generate form data objects with random subsets of fields missing/present
    - Verify required field errors are reported correctly and valid forms are accepted

- [x] 4. Checkpoint - Validation module complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement API client module
  - [x] 5.1 Create `webui/js/api.js` with HTTP client functions
    - Implement internal `_apiBaseUrl` variable and `setApiBaseUrl(url)` function
    - Implement `getAllCases()` — GET `/cases/`, returns `{ok, data?, error?, status?}`
    - Implement `createCase(caseData)` — POST `/cases/`, returns `{ok, data?, error?, status?}`
    - Implement `updateCase(caseId, caseData)` — PUT `/cases/{caseId}`, returns `{ok, data?, error?, status?}`
    - Implement `deleteCase(caseId)` — DELETE `/cases/{caseId}`, returns `{ok, error?, status?}`
    - All requests use a 10-second `AbortController` timeout
    - Handle network errors (fetch throws), timeout (abort), and HTTP error status codes
    - Error responses include status code or network error type in the error message
    - _Requirements: 3.4, 4.2, 5.3, 6.3, 7.1, 7.2_

  - [x] 5.2 Write property test for error message includes status information
    - **Property 6: Error message includes status information**
    - **Validates: Requirements 3.4**
    - Use fast-check to generate random HTTP error status codes (400-599)
    - Verify the formatted error message contains the numeric status code

- [x] 6. Implement UI rendering module
  - [x] 6.1 Create `webui/js/ui.js` with DOM rendering functions
    - Implement `renderCaseList(cases)` — renders table/list of cases with severity badges, truncated issue/response text, edit and delete action buttons per case
    - Implement `renderEmptyState()` — shows "no cases" message when list is empty
    - Implement `showCreateForm()` / `showEditForm(caseData)` — shows form in create or edit mode, populates fields for edit
    - Implement `clearForm()` — resets all form fields
    - Implement `showMessage(text, type)` — renders success/error messages in ARIA live region, auto-dismiss success after 5 seconds
    - Implement `showLoading()` / `hideLoading()` — manages loading indicator visibility
    - Implement `setSubmitDisabled(disabled)` / `setDeleteDisabled(caseId, disabled)` — manages button disabled states
    - Implement `showConnectivityError(retryCallback)` — shows error banner with retry button
    - Implement `hideConnectivityError()` — removes connectivity error banner
    - Implement `showValidationErrors(errors)` — shows inline errors adjacent to form fields
    - Manage focus movement after actions (form submit, delete, dialog)
    - _Requirements: 3.1, 3.2, 3.3, 3.5, 3.6, 4.3, 4.4, 4.8, 5.1, 5.4, 5.5, 5.6, 6.1, 6.4, 6.5, 6.7, 6.8, 7.1, 7.2, 7.3, 7.4, 8.5, 8.6_

  - [x] 6.2 Write property test for form population round-trip
    - **Property 7: Form population preserves case data**
    - **Validates: Requirements 5.1**
    - Use fast-check to generate valid Case objects with random field values
    - Mock DOM elements, populate the form, read values back, verify equality

- [x] 7. Implement application controller
  - [x] 7.1 Create `webui/js/app.js` with initialization and event wiring
    - Implement `init()` — reads API URL from localStorage (default `http://localhost:8000`), sets base URL on api module, loads initial case list
    - Wire settings form: validate URL, persist to localStorage, update api module — no page reload needed
    - Wire create form submit: validate via `validateCaseForm`, call `createCase`, show success/error, refresh list, clear form
    - Wire edit form submit: validate, call `updateCase`, show success/error, refresh list
    - Wire delete buttons: show confirmation dialog identifying the case, on confirm call `deleteCase`, on cancel do nothing
    - Wire refresh button: reload case list from API
    - Disable submit/delete buttons during in-flight requests
    - Handle connectivity errors: show error banner with retry, auto-remove on successful response
    - Call `init()` on DOMContentLoaded
    - _Requirements: 2.2, 2.3, 2.4, 3.1, 3.5, 4.3, 4.4, 4.5, 4.8, 5.4, 5.5, 5.6, 6.2, 6.4, 6.5, 6.6, 6.7, 6.8, 7.1, 7.2, 7.4, 8.6_

  - [x] 7.2 Write property test for API URL persistence round-trip
    - **Property 5: API URL persistence round-trip**
    - **Validates: Requirements 2.3, 2.4**
    - Use fast-check to generate valid URLs (passing validateApiUrl)
    - Mock localStorage, store and retrieve, verify identity

- [x] 8. Checkpoint - Full Web UI integration
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Set up property-based test infrastructure
  - [x] 9.1 Create `webui/tests/` directory with fast-check test files
    - Create `webui/package.json` with fast-check as a dev dependency and a test script using Node.js test runner (`node --test`)
    - Create `webui/tests/validation.test.js` aggregating property tests for Properties 1-5
    - Create `webui/tests/api.test.js` for Property 6 (error message formatting)
    - Create `webui/tests/ui.test.js` for Property 7 (form population round-trip with DOM mocks)
    - Each test file tags properties with format: `Feature: cases-webui, Property N: {title}`
    - Minimum 100 iterations per property
    - _Requirements: 2.1, 2.5, 3.2, 3.4, 4.5, 4.7, 5.1, 5.2_

- [x] 10. Final checkpoint - All tests passing
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- The Web UI uses plain JavaScript (no framework, no build step) loaded via `<script>` tags
- fast-check tests run in Node.js and only test the pure validation/utility functions
- CORS must be enabled on the FastAPI backend before the Web UI can make cross-origin requests
- The `webui/package.json` is only for test tooling — the Web UI itself has no runtime dependencies

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "2.2", "3.1"] },
    { "id": 1, "tasks": ["3.2", "3.3", "3.4", "3.5", "5.1"] },
    { "id": 2, "tasks": ["5.2", "6.1"] },
    { "id": 3, "tasks": ["6.2", "7.1"] },
    { "id": 4, "tasks": ["7.2", "9.1"] }
  ]
}
```

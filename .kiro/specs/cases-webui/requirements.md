# Requirements Document

## Introduction

A simple web-based user interface for managing support cases. The Web_UI lives in a separate `webui/` directory at the repository root and consumes the existing Cases REST API. It is built with plain HTML, CSS, and JavaScript (no heavy frameworks) and allows users to view, create, update, and delete support cases. The API base URL is configurable so the Web_UI can point to any deployment of the Cases API.

## Glossary

- **Web_UI**: The browser-based frontend application located in the `webui/` directory that provides a graphical interface for managing support cases.
- **Cases_API**: The existing FastAPI-based REST API served at `/cases` that provides CRUD operations for support case resources.
- **API_Base_URL**: A user-configurable string representing the root URL of the Cases_API (e.g., `http://localhost:8000`).
- **Case**: A support ticket entity with fields: case_id (UUID), email (string), issue (string), response (string), and severity (low/medium/high/critical).
- **Case_List_View**: The page or section of the Web_UI that displays all existing support cases.
- **Case_Form**: The form component used for creating or editing a support case.

## Requirements

### Requirement 1: Project Structure

**User Story:** As a developer, I want the web UI to live in its own directory separate from the API code, so that the frontend and backend remain independently maintainable.

#### Acceptance Criteria

1. THE Web_UI SHALL reside in a `webui/` directory at the repository root, separate from the `app/` directory.
2. THE Web_UI SHALL consist of plain HTML, CSS, and JavaScript files that require no transpilation, bundling, or package manager to run, and SHALL not depend on any framework that requires a build step or installation command.
3. THE Web_UI SHALL be servable by any static file server or by opening `webui/index.html` directly in a browser, with `index.html` serving as the single entry point that loads all required CSS and JavaScript files.
4. THE Web_UI directory SHALL contain at minimum: an `index.html` file, at least one CSS file for styling, and at least one JavaScript file for application logic.

### Requirement 2: Configurable API URL

**User Story:** As a developer, I want to configure the API base URL without modifying source code, so that the Web_UI can connect to different API deployments.

#### Acceptance Criteria

1. THE Web_UI SHALL provide a mechanism for the user to set the API_Base_URL at runtime, accepting only values that begin with `http://` or `https://` and do not exceed 2048 characters in length.
2. IF no API_Base_URL value exists in the browser's local storage and no custom value has been entered by the user, THEN THE Web_UI SHALL default the API_Base_URL to `http://localhost:8000`.
3. WHEN the user changes the API_Base_URL, THE Web_UI SHALL use the new value for all subsequent API requests without requiring a page reload of the full application.
4. THE Web_UI SHALL persist the configured API_Base_URL in the browser's local storage so it survives page reloads.
5. IF the user submits an API_Base_URL value that does not begin with `http://` or `https://` or exceeds 2048 characters, THEN THE Web_UI SHALL display an error message indicating the URL format is invalid and SHALL NOT update the stored API_Base_URL.

### Requirement 3: View All Cases

**User Story:** As a support agent, I want to see a list of all support cases, so that I can get an overview of current tickets.

#### Acceptance Criteria

1. WHEN the Web_UI loads, THE Case_List_View SHALL fetch and display all cases from the Cases_API `GET /cases/` endpoint.
2. THE Case_List_View SHALL display for each case: case_id, email, issue (truncated to 50 characters with a trailing ellipsis if longer), severity, and response (truncated to 50 characters with a trailing ellipsis if longer).
3. THE Case_List_View SHALL visually distinguish severity levels (low, medium, high, critical) by applying a unique colour or badge style to each level.
4. WHEN the Cases_API returns an error, THE Web_UI SHALL display an error message that includes the HTTP status code or network error type so the user can identify the nature of the failure.
5. THE Case_List_View SHALL provide a refresh mechanism to reload the case list from the Cases_API.
6. IF the Cases_API returns an empty list, THEN THE Case_List_View SHALL display a message indicating that no cases exist.

### Requirement 4: Create a Case

**User Story:** As a support agent, I want to create a new support case through the UI, so that I can log incoming issues.

#### Acceptance Criteria

1. THE Web_UI SHALL provide a Case_Form for creating a new case with fields: email (max 254 characters), issue (max 2000 characters), severity, and an optional response (max 5000 characters).
2. WHEN the user submits a valid Case_Form, THE Web_UI SHALL send a `POST /cases/` request to the Cases_API with the form data.
3. WHEN the Cases_API responds with a 201 status, THE Web_UI SHALL display a visible success message, clear the Case_Form fields, and refresh the Case_List_View.
4. WHEN the Cases_API responds with a 400 or 422 status, THE Web_UI SHALL display the validation error message returned by the API adjacent to the Case_Form without clearing the user's input.
5. THE Case_Form SHALL prevent submission and display a visual required-field indicator for each empty required field (email, issue, severity) when the user attempts to submit.
6. THE Case_Form SHALL restrict severity to one of: low, medium, high, critical, using a constrained input control that does not allow free-text entry.
7. THE Case_Form SHALL validate that the email field matches a valid email format (contains exactly one `@` separating non-empty local and domain parts) before submission and display an inline validation error if the format is invalid.
8. WHILE a Case_Form submission request is in progress, THE Web_UI SHALL disable the submit button to prevent duplicate submissions.

### Requirement 5: Update a Case

**User Story:** As a support agent, I want to edit an existing support case, so that I can add responses or correct information.

#### Acceptance Criteria

1. WHEN the user selects a case for editing, THE Web_UI SHALL populate the Case_Form with the current values of that case's email, issue, response, and severity fields, and SHALL NOT allow editing of the case_id.
2. THE Case_Form for updating SHALL enforce that email, issue, and severity are required fields before submission, and SHALL restrict severity to one of: low, medium, high, critical.
3. WHEN the user submits an updated Case_Form, THE Web_UI SHALL send a `PUT /cases/{case_id}` request to the Cases_API including all fields: email, issue, response, and severity.
4. WHEN the Cases_API responds with a 200 status, THE Web_UI SHALL display a success indication and refresh the Case_List_View.
5. WHEN the Cases_API responds with a 404 status, THE Web_UI SHALL inform the user that the case no longer exists and refresh the Case_List_View.
6. WHEN the Cases_API responds with a 400 or 422 status, THE Web_UI SHALL display the validation error message returned by the API.

### Requirement 6: Delete a Case

**User Story:** As a support agent, I want to delete a support case, so that I can remove resolved or invalid tickets.

#### Acceptance Criteria

1. THE Web_UI SHALL provide a delete action for each case in the Case_List_View.
2. WHEN the user initiates a delete action, THE Web_UI SHALL prompt for confirmation that identifies the target case before proceeding.
3. WHEN the user confirms deletion, THE Web_UI SHALL send a `DELETE /cases/{case_id}` request to the Cases_API.
4. WHEN the Cases_API responds with a 204 status, THE Web_UI SHALL remove the case from the Case_List_View and display a success indication.
5. WHEN the Cases_API responds with a 404 status, THE Web_UI SHALL inform the user that the case was not found and refresh the Case_List_View.
6. IF the user cancels the confirmation prompt, THEN THE Web_UI SHALL take no further action and leave the Case_List_View unchanged.
7. IF the Cases_API responds with a 500 status during a delete request, THEN THE Web_UI SHALL display an error message indicating the deletion failed.
8. WHILE a delete request is in progress, THE Web_UI SHALL disable the delete action for the targeted case to prevent duplicate submissions.

### Requirement 7: Error Handling and Connectivity

**User Story:** As a support agent, I want clear feedback when the API is unreachable, so that I know when the system is unavailable.

#### Acceptance Criteria

1. IF the Cases_API is unreachable (network error or no response within 10 seconds), THEN THE Web_UI SHALL display a connectivity error message indicating the API cannot be reached.
2. IF a request to the Cases_API does not receive a response within 10 seconds, THEN THE Web_UI SHALL display a retry button that re-sends the same request when activated.
3. WHILE a request to the Cases_API is in progress, THE Web_UI SHALL display a visible loading indicator until the response is received or the request fails.
4. WHEN the Cases_API responds successfully after a connectivity error was displayed, THE Web_UI SHALL remove the connectivity error message.

### Requirement 8: Accessibility

**User Story:** As a user with assistive technology, I want the Web_UI to be navigable and operable, so that I can manage cases effectively.

#### Acceptance Criteria

1. THE Web_UI SHALL use semantic HTML elements (headings, labels, buttons, tables or lists) for content structure.
2. THE Case_Form SHALL associate labels with form inputs using `for`/`id` attributes.
3. THE Web_UI SHALL ensure all interactive elements are reachable via the Tab key in a logical reading order and operable via Enter or Space keys without requiring a mouse.
4. THE Web_UI SHALL provide focus indicators on interactive elements that are visually distinct from the element's default unfocused state.
5. WHEN the Web_UI displays a success message, error message, or removes an item from the Case_List_View, THE Web_UI SHALL announce the change to assistive technologies using an ARIA live region.
6. WHEN a user-initiated action causes a UI change (confirmation dialog appearing, form submission completing, or case deletion completing), THE Web_UI SHALL move focus to the relevant updated element or container.

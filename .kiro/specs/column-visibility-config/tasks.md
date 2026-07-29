# Implementation Plan: Column Visibility Configuration

## Overview

Implement a configuration-driven column visibility mechanism for the support cases table. A new `config.js` file exposes `AppConfig.columnVisibility`, and the `renderCaseList` function in `ui.js` is refactored to consult this configuration at render time. The design follows a fail-open strategy where any misconfiguration defaults to showing all columns.

## Tasks

- [x] 1. Create configuration file and update script loading
  - [x] 1.1 Create `webui/js/config.js` with the `AppConfig` global object
    - Define `AppConfig` with `columnVisibility` property
    - Set all six column identifiers (`caseId`, `email`, `issue`, `severity`, `response`, `actions`) to `true`
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 1.2 Add `config.js` script tag to `webui/index.html` before all other application scripts
    - Insert `<script src="js/config.js"></script>` before the `validation.js` script tag
    - _Requirements: 2.1_

- [x] 2. Implement column visibility logic in `ui.js`
  - [x] 2.1 Add `isColumnVisible` helper function to `webui/js/ui.js`
    - Implement the visibility resolution logic that returns `true` unless config explicitly sets `false`
    - Handle missing `AppConfig`, missing `columnVisibility`, missing keys, and non-boolean values
    - Export via the `module.exports` block for testability
    - _Requirements: 3.1, 4.1, 4.2, 5.1, 5.2_

  - [x] 2.2 Refactor `renderCaseList` in `webui/js/ui.js` to use column definitions array
    - Define a `columns` array with `id`, `header`, and `render` properties for each column
    - Filter the array using `isColumnVisible` to get `visibleColumns`
    - Replace the hardcoded header loop with iteration over `visibleColumns`
    - Replace the hardcoded cell creation with iteration over `visibleColumns` and their render functions
    - Preserve existing class names, data attributes, and behavior for each cell type
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 2.3 Write property test: Visible column count matches configuration
    - **Property 1: Visible column count matches configuration**
    - Generate random `columnVisibility` configs and verify `<th>` count equals number of `true`-resolving columns
    - **Validates: Requirements 3.2, 3.4**

  - [x] 2.4 Write property test: Hidden columns produce no cells
    - **Property 2: Hidden columns produce no cells**
    - Generate configs with columns set to `false` and verify zero header/data cells for those columns
    - **Validates: Requirements 3.2, 3.3**

  - [x] 2.5 Write property test: Row cell count matches header count
    - **Property 3: Row cell count matches header count**
    - Generate random configs and case arrays, verify every `<tr>` in tbody has same `<td>` count as `<th>` count in thead
    - **Validates: Requirements 3.2, 3.3, 3.4**

- [x] 3. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement default and error handling behavior
  - [x] 4.1 Write unit tests for default and invalid configuration scenarios
    - Test: `AppConfig` undefined → 6 columns rendered
    - Test: `columnVisibility` missing → 6 columns rendered
    - Test: column identifier absent from config → that column is visible
    - Test: non-boolean value for a column → that column is visible
    - Test: unknown keys in config → ignored, valid columns render normally
    - _Requirements: 4.1, 4.2, 5.1, 5.2_

  - [x] 4.2 Write property test: Missing or invalid config defaults to all-visible
    - **Property 4: Missing or invalid config defaults to all-visible**
    - Generate cases where `AppConfig` is undefined, `columnVisibility` is missing, keys are absent, or values are non-boolean — verify 6 headers rendered
    - **Validates: Requirements 4.1, 4.2, 5.1**

  - [x] 4.3 Write property test: Unknown keys are ignored
    - **Property 5: Unknown keys are ignored**
    - Generate `columnVisibility` objects with extra non-matching keys and verify table renders identically to a config without those keys
    - **Validates: Requirements 5.2**

- [x] 5. Integration wiring and final verification
  - [x] 5.1 Write unit tests for end-to-end rendering scenarios
    - Test: hiding `email` and `severity` produces a 4-column table
    - Test: all columns hidden produces empty table structure (thead/tbody with no cells)
    - Test: default config (all `true`) matches original 6-column behavior
    - Test: script order in `index.html` has `config.js` before `validation.js`, `api.js`, `ui.js`, `app.js`
    - _Requirements: 1.1, 2.1, 3.2, 3.3, 3.4_

- [x] 6. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using fast-check 3.22.0
- Unit tests validate specific examples and edge cases
- All test files go in `webui/tests/` following the existing project convention
- JavaScript is the implementation language (matching existing webui code)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2"] },
    { "id": 3, "tasks": ["2.3", "2.4", "2.5", "4.1"] },
    { "id": 4, "tasks": ["4.2", "4.3", "5.1"] }
  ]
}
```

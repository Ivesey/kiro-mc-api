# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Table Structure and Severity Badge Rendering
  - **IMPORTANT**: Write this property-based test BEFORE implementing the fix
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Use fast-check to generate random case arrays (non-empty) and verify the DOM output structure
  - **Test file**: `webui/tests/ui.render.test.js` (new file, uses node:test + fast-check like existing tests)
  - **DOM mock**: Create a mock DOM that tracks element creation (createElement, appendChild) to inspect the tree structure produced by `renderCaseList`
  - Test assertions (expected behavior that WILL FAIL on unfixed code):
    - `renderCaseList(cases)` produces a `table` element with class `case-list` inside `#case-list`
    - The table contains a `thead` with a `tr` containing 6 `th` elements: Case ID, Email, Issue, Severity, Response, Actions
    - The table contains a `tbody` with one `tr` per case
    - Each `tr` contains `td` cells (not `span` elements)
    - Severity badge class matches pattern `severity-badge severity-badge--{level}` (BEM double-dash)
  - Bug condition from design: `isBugCondition(input)` — cases array is non-empty AND rendered DOM contains `div[role="listitem"]` instead of table elements OR severity badge class does NOT match `/severity-badge--\w+/`
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct — it proves the bug exists)
  - Document counterexamples found: DOM contains `div.case-item` with `span` children instead of `table > tbody > tr > td`; severity class is `severity-badge severity-high` instead of `severity-badge severity-badge--high`
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Table Behaviors Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - **Test file**: `webui/tests/ui.render.test.js` (append to the same file)
  - **DOM mock**: Extend the mock DOM to track function calls (`renderEmptyState`) and attribute assignments
  - Observe behavior on UNFIXED code for non-buggy inputs:
    - Observe: `renderCaseList([])` hides case-list and shows empty-state
    - Observe: `renderCaseList(null)` hides case-list and shows empty-state
    - Observe: `renderCaseList(undefined)` hides case-list and shows empty-state
    - Observe: For any non-empty cases, Edit button has `data-case-id` matching `caseItem.case_id`
    - Observe: For any non-empty cases, Delete button has `data-case-id` matching `caseItem.case_id`
    - Observe: Issue text is truncated via `truncateText(issue, 50)` — output length ≤ 50
    - Observe: Response text is truncated via `truncateText(response, 50)` — output length ≤ 50
  - Write property-based tests (fast-check) capturing observed behavior:
    - Property: For all empty/null/undefined inputs, `renderEmptyState()` is triggered (empty-state shown, case-list hidden)
    - Property: For all non-empty case arrays, each case has Edit and Delete buttons with correct `data-case-id`
    - Property: For all non-empty case arrays, issue and response text in rendered output have length ≤ 50 (truncateText applied)
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 3. Fix for case list table rendering and severity badge classes

  - [x] 3.1 Rewrite `renderCaseList` to use table elements
    - In `webui/js/ui.js`, replace the `div`/`span` rendering logic with proper table structure
    - Create a `table` element with `className = 'case-list'`
    - Create `thead` containing a `tr` with `th` elements for: Case ID, Email, Issue, Severity, Response, Actions
    - Create `tbody` to contain case data rows
    - For each case, create a `tr` instead of `div[role="listitem"]`
    - For each field, create `td` instead of `span`
    - Add class `actions` to the actions `td` cell
    - Append table to `caseList` container after clearing innerHTML
    - Keep `emptyState.hidden = true` and `caseList.hidden = false` logic unchanged
    - _Bug_Condition: isBugCondition(input) where cases.length > 0 AND DOM uses div/span instead of table/tr/td_
    - _Expected_Behavior: Container has table.case-list > thead > tr > th[6] + tbody > tr[cases.length] > td_
    - _Preservation: Empty state handling, Edit/Delete buttons, truncateText usage unchanged_
    - _Requirements: 2.1, 2.2_

  - [x] 3.2 Fix severity badge class to use BEM double-dash modifier
    - Change `'severity-badge severity-' + caseItem.severity` to `'severity-badge severity-badge--' + caseItem.severity`
    - This ensures CSS selectors `.severity-badge--low`, `.severity-badge--medium`, `.severity-badge--high`, `.severity-badge--critical` match
    - _Bug_Condition: severityBadge.className does NOT match /severity-badge--\w+/_
    - _Expected_Behavior: severityBadge.className === 'severity-badge severity-badge--' + level_
    - _Requirements: 2.3_

  - [x] 3.3 Preserve Edit/Delete buttons with data-case-id and truncateText usage
    - Ensure Edit and Delete buttons are created as before with `data-case-id` attribute set to `caseItem.case_id`
    - Ensure `truncateText(caseItem.issue || '', 50)` and `truncateText(caseItem.response || '', 50)` are still used for issue and response cells
    - _Preservation: Buttons and truncation behavior from original code carried forward_
    - _Requirements: 3.2, 3.3_

  - [x] 3.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Table Structure and Severity Badge Rendering
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior (table structure, BEM severity classes)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1: `node --test webui/tests/ui.render.test.js`
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.5 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Table Behaviors Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run preservation property tests from step 2: `node --test webui/tests/ui.render.test.js`
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm empty-state handling, button attributes, and truncateText still work after fix
    - Also run existing ui.test.js to confirm showEditForm property still passes: `node --test webui/tests/ui.test.js`
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full webui test suite: `node --test webui/tests/validation.test.js webui/tests/api.test.js webui/tests/ui.test.js webui/tests/app.test.js webui/tests/ui.render.test.js`
  - Ensure all tests pass, ask the user if questions arise
  - Verify no regressions in existing tests (especially Property 7: Form population preserves case data)

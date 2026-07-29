# Case List Table Render Bugfix Design

## Overview

The `renderCaseList` function in `webui/js/ui.js` renders cases using `div` and `span` elements instead of semantic HTML table elements. The CSS in `styles.css` already targets `.case-list th`, `.case-list td`, and `.case-list tr:hover`, but these selectors never match because the DOM contains only `div`/`span` elements. Additionally, severity badge classes use a single-dash pattern (`severity-badge severity-{level}`) while the CSS defines BEM double-dash modifiers (`.severity-badge--{level}`). The fix converts the rendering to proper `table`/`thead`/`tbody`/`tr`/`th`/`td` elements and corrects the severity badge class construction.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — when `renderCaseList` is called with a non-empty array of cases, the output DOM uses `div`/`span` instead of table elements, and severity badge classes use single-dash instead of BEM double-dash
- **Property (P)**: The desired behavior — proper HTML table structure with `thead`/`tbody`/`tr`/`th`/`td` elements and BEM-compliant severity badge classes
- **Preservation**: Existing empty-state handling, Edit/Delete buttons with `data-case-id`, `truncateText` usage, and `showEditForm` behavior must remain unchanged
- **renderCaseList**: The function in `webui/js/ui.js` that renders the case list into `#case-list`
- **truncateText**: The function in `webui/js/validation.js` that truncates strings to a given length
- **BEM modifier**: CSS naming convention using double-dash (`--`) for element modifiers (e.g., `severity-badge--high`)

## Bug Details

### Bug Condition

The bug manifests when `renderCaseList` is called with a non-empty array of cases. The function creates `div[role="listitem"]` elements with `span` children instead of a `table` with `thead`/`tbody`/`tr`/`th`/`td` elements. Additionally, severity badge classes are constructed as `severity-badge severity-{level}` (single dash) instead of `severity-badge severity-badge--{level}` (BEM double-dash modifier).

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type { cases: Array<Case>, container: HTMLElement }
  OUTPUT: boolean
  
  RETURN input.cases IS NOT NULL
         AND input.cases.length > 0
         AND (renderedDOM contains DIV[role="listitem"] instead of TABLE/TR/TD
              OR severityBadge.className does NOT match /severity-badge--\w+/)
END FUNCTION
```

### Examples

- **Example 1**: `renderCaseList([{case_id: "C001", email: "a@b.com", issue: "Login fails", severity: "high", response: ""}])` → Creates `div.case-item` with `span` children. Expected: Creates `table.case-list > tbody > tr > td` elements.
- **Example 2**: A case with `severity: "critical"` gets class `severity-badge severity-critical`. Expected: class `severity-badge severity-badge--critical`.
- **Example 3**: A case with `severity: "low"` gets class `severity-badge severity-low`. Expected: class `severity-badge severity-badge--low`. The green badge styling from `.severity-badge--low` never applies.
- **Edge case**: `renderCaseList([])` → Calls `renderEmptyState()`. This is NOT affected by the bug (correct behavior already).

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Empty state rendering (`renderEmptyState()`) must continue to be called when cases array is empty or null/undefined
- Edit and Delete buttons must continue to have `data-case-id` attributes matching each case's `case_id`
- Issue and response text must continue to be truncated to 50 characters via `truncateText`
- `showEditForm` must continue to populate form fields with case values (existing property tests must keep passing)
- The `module.exports` block must continue to export all functions for Node.js testing

**Scope:**
All inputs that do NOT involve rendering a non-empty case list should be completely unaffected by this fix. This includes:
- Empty array or null/undefined inputs to `renderCaseList`
- All other exported UI functions (`showEditForm`, `clearForm`, `showMessage`, etc.)
- Event handler wiring and button behavior

## Hypothesized Root Cause

Based on the bug description, the issues are:

1. **Incorrect Element Types**: `renderCaseList` creates `div` and `span` elements instead of `table`, `thead`, `tbody`, `tr`, `th`, and `td` elements. The CSS was written for table elements but the JS was never updated to match.

2. **Missing Table Header Row**: No `thead` with column headers (Case ID, Email, Issue, Severity, Response, Actions) is rendered, so `th` styles never apply.

3. **Incorrect Severity Class Construction**: The class string is built with string concatenation as `'severity-badge severity-' + caseItem.severity` which produces `severity-badge severity-high`. It should be `'severity-badge severity-badge--' + caseItem.severity` to match the BEM CSS selectors.

4. **Missing Table Wrapper**: The function appends items directly to the `#case-list` container div without creating a `table` element with the `case-list` class, so `.case-list th` and `.case-list td` selectors cannot match.

## Correctness Properties

Property 1: Bug Condition - Table Structure Rendering

_For any_ non-empty array of cases passed to `renderCaseList`, the fixed function SHALL render a `table` element with class `case-list` containing a `thead` row with `th` headers (Case ID, Email, Issue, Severity, Response, Actions) and a `tbody` containing one `tr` per case with `td` cells for each data field, and severity badges SHALL have class `severity-badge severity-badge--{level}`.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Non-Table Behaviors Unchanged

_For any_ input to `renderCaseList` or other UI functions, the fixed code SHALL produce the same result as the original code for: empty-state handling (empty/null/undefined cases), Edit/Delete button presence with correct `data-case-id` attributes, `truncateText` application to issue and response fields, and `showEditForm` field population.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `webui/js/ui.js`

**Function**: `renderCaseList`

**Specific Changes**:

1. **Create table element**: Instead of appending `div` items directly to `caseList`, create a `table` element with `className = 'case-list'`.

2. **Add thead with column headers**: Create a `thead` containing a single `tr` with `th` elements for: Case ID, Email, Issue, Severity, Response, Actions.

3. **Create tbody for data rows**: Create a `tbody` element to contain case rows.

4. **Replace div/span with tr/td**: For each case, create a `tr` instead of `div[role="listitem"]`, and create `td` elements instead of `span` elements.

5. **Fix severity badge class**: Change `'severity-badge severity-' + caseItem.severity` to `'severity-badge severity-badge--' + caseItem.severity`.

6. **Add actions class to actions cell**: The actions `td` should have class `actions` to match the `.case-list td.actions` CSS selector.

7. **Append table to container**: Replace `caseList` innerHTML, then append the constructed `table` element to `caseList`.

8. **Preserve Edit/Delete buttons**: Keep `data-case-id` attributes on both Edit and Delete buttons exactly as before.

9. **Preserve truncateText usage**: Keep `truncateText(caseItem.issue || '', 50)` and `truncateText(caseItem.response || '', 50)` calls unchanged.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that call `renderCaseList` with case data and inspect the resulting DOM structure. Run these tests on the UNFIXED code to observe failures and confirm the root cause.

**Test Cases**:
1. **Table Element Test**: Assert the container has a `table` child element (will fail on unfixed code — gets `div` instead)
2. **Thead/Th Test**: Assert the table has a `thead` with `th` elements for all column headers (will fail on unfixed code — no `thead` exists)
3. **Tbody/Tr/Td Test**: Assert each case is rendered as a `tr` with `td` cells (will fail on unfixed code — gets `div`/`span`)
4. **Severity Badge Class Test**: Assert severity badge has class `severity-badge--{level}` (will fail on unfixed code — gets `severity-{level}`)

**Expected Counterexamples**:
- DOM contains `div[role="listitem"]` instead of `tr` elements
- No `table`, `thead`, or `tbody` elements exist in the rendered output
- Severity badge class is `severity-badge severity-high` instead of `severity-badge severity-badge--high`

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := renderCaseList_fixed(input.cases)
  ASSERT container contains TABLE with class "case-list"
  ASSERT TABLE contains THEAD with TH headers
  ASSERT TABLE contains TBODY with TR count == input.cases.length
  ASSERT each TR contains TD cells with correct case data
  ASSERT severity badge class matches "severity-badge severity-badge--{level}"
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT renderCaseList_fixed(input) = renderCaseList_original(input)
END FOR

FOR ALL caseData DO
  ASSERT showEditForm_fixed(caseData) = showEditForm_original(caseData)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for empty states, button attributes, and text truncation, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Empty State Preservation**: Verify `renderCaseList([])`, `renderCaseList(null)`, and `renderCaseList(undefined)` still call `renderEmptyState()` after fix
2. **Button Attributes Preservation**: Verify Edit/Delete buttons still have correct `data-case-id` attributes after fix
3. **TruncateText Preservation**: Verify issue and response text are still truncated to 50 chars via `truncateText` after fix
4. **ShowEditForm Preservation**: Verify `showEditForm` still populates all fields correctly after fix

### Unit Tests

- Test that `renderCaseList` with non-empty cases produces `table > thead + tbody` structure
- Test that `thead` contains correct column headers in order
- Test that each `tbody > tr` contains correct `td` cells with case data
- Test severity badge class is `severity-badge severity-badge--{level}` for each severity level
- Test empty/null/undefined cases still trigger `renderEmptyState()`
- Test Edit/Delete buttons have `data-case-id` matching the case

### Property-Based Tests

- Generate random arrays of case objects and verify table structure is always correct (correct number of rows, correct `td` count per row)
- Generate random severity values from {low, medium, high, critical} and verify badge class always uses BEM double-dash pattern
- Generate random string lengths for issue/response and verify `truncateText` is always applied with max 50 chars
- Generate empty/null/undefined inputs and verify empty state is always rendered

### Integration Tests

- Test full render cycle: load cases from API → render table → verify DOM matches expected structure
- Test that CSS selectors (`.case-list th`, `.case-list td`, `.case-list tr:hover`) actually match rendered elements
- Test that severity badge colors are visually applied (computed styles match CSS definitions)

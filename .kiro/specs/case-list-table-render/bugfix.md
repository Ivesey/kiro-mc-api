# Bugfix Requirements Document

## Introduction

The `renderCaseList` function in `webui/js/ui.js` renders cases using `div` and `span` elements instead of proper HTML table elements (`table`, `thead`, `tbody`, `tr`, `th`, `td`). The CSS in `styles.css` already defines table-specific styles targeting `.case-list th`, `.case-list td`, and `.case-list tr:hover`, but these selectors never match because the DOM contains no table elements. Additionally, severity badge classes are constructed as `severity-badge severity-{level}` (space-separated, single dash) in JS, while the CSS defines them as `severity-badge--{level}` (BEM double-dash modifier). The result is an unstructured, unstyled list of case data on a single line per case.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN `renderCaseList` is called with a non-empty array of cases THEN the system renders each case as a `div[role="listitem"]` with `span` children instead of a table with `thead`/`tbody`/`tr`/`th`/`td` elements

1.2 WHEN `renderCaseList` is called with a non-empty array of cases THEN the CSS table styles (`.case-list th`, `.case-list td`, `.case-list tr:hover`) do not apply because no matching elements exist in the DOM

1.3 WHEN `renderCaseList` renders a severity badge THEN the system assigns class `severity-badge severity-{level}` (single dash, space-separated) which does not match the CSS selectors `.severity-badge--{level}` (double-dash BEM modifier)

### Expected Behavior (Correct)

2.1 WHEN `renderCaseList` is called with a non-empty array of cases THEN the system SHALL render a `table` element with class `case-list` containing a `thead` with column headers (Case ID, Email, Issue, Severity, Response, Actions) and a `tbody` with one `tr` per case, each containing `td` cells for the case data

2.2 WHEN `renderCaseList` is called with a non-empty array of cases THEN the CSS table styles (`.case-list th`, `.case-list td`, `.case-list tr:hover`) SHALL apply to the rendered table elements, providing proper tabular layout with borders, padding, and hover highlighting

2.3 WHEN `renderCaseList` renders a severity badge THEN the system SHALL assign classes `severity-badge severity-badge--{level}` (base class plus BEM double-dash modifier) so that the CSS color and border styles for each severity level apply correctly

### Unchanged Behavior (Regression Prevention)

3.1 WHEN `renderCaseList` is called with an empty array or null/undefined THEN the system SHALL CONTINUE TO call `renderEmptyState()` to show the empty state message

3.2 WHEN `renderCaseList` is called with cases THEN each row SHALL CONTINUE TO contain Edit and Delete buttons with `data-case-id` attributes matching the case's `case_id`

3.3 WHEN `renderCaseList` is called with cases THEN issue and response text SHALL CONTINUE TO be truncated to 50 characters via `truncateText`

3.4 WHEN `showEditForm` is called with case data THEN the system SHALL CONTINUE TO populate form fields with the case's values unchanged (existing property test must keep passing)

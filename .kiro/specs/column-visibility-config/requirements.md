# Requirements Document

## Introduction

This feature allows a site administrator to configure which columns of the support cases table are visible. Visibility settings are defined in a `config.js` file that lives alongside the other UI scripts. By default, all columns are shown. The administrator hides columns by editing the configuration file.

## Glossary

- **Config_Module**: The JavaScript configuration file (`webui/js/config.js`) that exposes column visibility settings as a global object.
- **Column_Visibility_Setting**: A property within the configuration object that maps a column identifier to a boolean indicating whether the column is visible (`true`) or hidden (`false`).
- **Renderer**: The `renderCaseList` function in `webui/js/ui.js` responsible for building and displaying the cases table.
- **Column_Identifier**: A string key representing one of the table columns: `caseId`, `email`, `issue`, `severity`, `response`, `actions`.
- **Site_Administrator**: The person who edits the configuration file to control column visibility.

## Requirements

### Requirement 1: Configuration File Structure

**User Story:** As a site administrator, I want a dedicated configuration file that defines column visibility, so that I can control which columns appear in the cases table without modifying application code.

#### Acceptance Criteria

1. THE Config_Module SHALL expose a global object `AppConfig` with a `columnVisibility` property containing a Column_Visibility_Setting for each Column_Identifier.
2. THE Config_Module SHALL define Column_Visibility_Settings for these Column_Identifiers: `caseId`, `email`, `issue`, `severity`, `response`, `actions`.
3. THE Config_Module SHALL set each Column_Visibility_Setting to `true` by default.
4. THE Config_Module SHALL be located at `webui/js/config.js`.

### Requirement 2: Script Loading Order

**User Story:** As a site administrator, I want the configuration to load before other scripts, so that visibility settings are available when the table renders.

#### Acceptance Criteria

1. THE Config_Module SHALL be loaded via a `<script>` tag in `index.html` before all other application scripts (validation.js, api.js, ui.js, app.js).

### Requirement 3: Column Rendering Based on Configuration

**User Story:** As a site administrator, I want hidden columns to not appear in the rendered table, so that I can simplify the view for my users.

#### Acceptance Criteria

1. WHEN `renderCaseList` is called, THE Renderer SHALL read the `AppConfig.columnVisibility` settings to determine which columns to display.
2. WHEN a Column_Visibility_Setting is `false`, THE Renderer SHALL omit the corresponding header cell from the table header row.
3. WHEN a Column_Visibility_Setting is `false`, THE Renderer SHALL omit the corresponding data cell from each table body row.
4. WHEN a Column_Visibility_Setting is `true` or not present, THE Renderer SHALL include the corresponding header cell and data cells.

### Requirement 4: Default Behavior

**User Story:** As a site administrator, I want all columns to be visible by default, so that the table works as expected without any configuration changes.

#### Acceptance Criteria

1. WHEN `AppConfig` is not defined or `columnVisibility` is missing, THE Renderer SHALL display all columns.
2. WHEN a specific Column_Identifier is absent from `columnVisibility`, THE Renderer SHALL treat that column as visible.

### Requirement 5: Graceful Handling of Invalid Configuration

**User Story:** As a site administrator, I want the table to still render correctly even if I make a mistake in the configuration, so that the application remains usable.

#### Acceptance Criteria

1. IF `AppConfig.columnVisibility` contains a non-boolean value for a Column_Identifier, THEN THE Renderer SHALL treat that column as visible.
2. IF `AppConfig.columnVisibility` contains keys not matching any Column_Identifier, THEN THE Renderer SHALL ignore those keys.

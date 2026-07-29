/**
 * DOM rendering functions for the Cases Web UI.
 * Handles all visual updates: list rendering, form management, messages,
 * loading states, and focus management.
 */

/**
 * Determines whether a column should be visible based on AppConfig.columnVisibility.
 * Returns true (show column) unless the config explicitly sets the column to false.
 * Handles missing AppConfig, missing columnVisibility, missing keys, and non-boolean values.
 * @param {string} columnId - The column identifier to check
 * @returns {boolean} Whether the column should be visible
 */
function isColumnVisible(columnId) {
  if (typeof AppConfig === 'undefined' || !AppConfig) return true;
  if (!AppConfig.columnVisibility) return true;
  var value = AppConfig.columnVisibility[columnId];
  if (typeof value !== 'boolean') return true;
  return value;
}

/**
 * Renders the case list into #case-list.
 * Creates a table with thead/tbody containing one tr per case with td cells and action buttons.
 * Hides the empty state and shows the list.
 * @param {Array} cases - Array of case objects
 */
function renderCaseList(cases) {
  var caseList = document.getElementById('case-list');
  var emptyState = document.getElementById('empty-state');

  // Clear existing content
  caseList.innerHTML = '';

  if (!cases || cases.length === 0) {
    renderEmptyState();
    return;
  }

  // Hide empty state, show case list
  emptyState.hidden = true;
  caseList.hidden = false;

  // Column definitions array
  var columns = [
    { id: 'caseId', header: 'Case ID', render: function(caseItem) {
      var td = document.createElement('td');
      td.textContent = caseItem.case_id;
      return td;
    }},
    { id: 'email', header: 'Email', render: function(caseItem) {
      var td = document.createElement('td');
      td.textContent = caseItem.email;
      return td;
    }},
    { id: 'issue', header: 'Issue', render: function(caseItem) {
      var td = document.createElement('td');
      td.className = 'case-issue';
      td.textContent = truncateText(caseItem.issue || '', 50);
      return td;
    }},
    { id: 'severity', header: 'Severity', render: function(caseItem) {
      var td = document.createElement('td');
      var severityBadge = document.createElement('span');
      severityBadge.className = 'severity-badge severity-badge--' + caseItem.severity;
      severityBadge.textContent = caseItem.severity;
      td.appendChild(severityBadge);
      return td;
    }},
    { id: 'response', header: 'Response', render: function(caseItem) {
      var td = document.createElement('td');
      td.className = 'case-response';
      td.textContent = truncateText(caseItem.response || '', 50);
      return td;
    }},
    { id: 'actions', header: 'Actions', render: function(caseItem) {
      var td = document.createElement('td');
      td.className = 'actions';
      var editBtn = document.createElement('button');
      editBtn.type = 'button';
      editBtn.className = 'edit-button';
      editBtn.textContent = 'Edit';
      editBtn.setAttribute('data-case-id', caseItem.case_id);
      var deleteBtn = document.createElement('button');
      deleteBtn.type = 'button';
      deleteBtn.className = 'delete-button';
      deleteBtn.textContent = 'Delete';
      deleteBtn.setAttribute('data-case-id', caseItem.case_id);
      td.appendChild(editBtn);
      td.appendChild(deleteBtn);
      return td;
    }}
  ];

  // Filter columns by visibility configuration
  var visibleColumns = columns.filter(function(col) {
    return isColumnVisible(col.id);
  });

  // Create table structure
  var table = document.createElement('table');
  table.className = 'case-list';

  // Create thead with column headers
  var thead = document.createElement('thead');
  var headerRow = document.createElement('tr');
  visibleColumns.forEach(function(col) {
    var th = document.createElement('th');
    th.textContent = col.header;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Create tbody with case rows
  var tbody = document.createElement('tbody');

  cases.forEach(function(caseItem) {
    var row = document.createElement('tr');
    visibleColumns.forEach(function(col) {
      row.appendChild(col.render(caseItem));
    });
    tbody.appendChild(row);
  });

  table.appendChild(tbody);
  caseList.appendChild(table);
}

/**
 * Renders the empty state message when no cases exist.
 * Shows #empty-state and hides #case-list content.
 */
function renderEmptyState() {
  var emptyState = document.getElementById('empty-state');
  var caseList = document.getElementById('case-list');

  emptyState.hidden = false;
  caseList.hidden = true;
  caseList.innerHTML = '';
}

/**
 * Shows the create form.
 * Sets heading to "Create Case", clears form, sets submit button text,
 * and focuses the first input.
 */
function showCreateForm() {
  var formSection = document.getElementById('case-form-section');
  var heading = document.getElementById('case-form-heading');
  var submitBtn = document.getElementById('submit-case-button');
  var emailInput = document.getElementById('email-input');

  clearForm();
  formSection.hidden = false;
  heading.textContent = 'Create Case';
  submitBtn.textContent = 'Create Case';

  emailInput.focus();
}

/**
 * Shows the edit form populated with the given case data.
 * Sets heading to "Edit Case", populates fields, sets submit button text,
 * and focuses the first input.
 * @param {object} caseData - Case object with case_id, email, issue, severity, response
 */
function showEditForm(caseData) {
  var formSection = document.getElementById('case-form-section');
  var heading = document.getElementById('case-form-heading');
  var submitBtn = document.getElementById('submit-case-button');
  var caseIdField = document.getElementById('case-id-field');
  var emailInput = document.getElementById('email-input');
  var issueInput = document.getElementById('issue-input');
  var severityInput = document.getElementById('severity-input');
  var responseInput = document.getElementById('response-input');

  clearForm();
  formSection.hidden = false;
  heading.textContent = 'Edit Case';
  submitBtn.textContent = 'Update Case';

  caseIdField.value = caseData.case_id || '';
  emailInput.value = caseData.email || '';
  issueInput.value = caseData.issue || '';
  severityInput.value = caseData.severity || '';
  responseInput.value = caseData.response || '';

  emailInput.focus();
}

/**
 * Clears all form fields and removes validation error messages.
 */
function clearForm() {
  var caseIdField = document.getElementById('case-id-field');
  var emailInput = document.getElementById('email-input');
  var issueInput = document.getElementById('issue-input');
  var severityInput = document.getElementById('severity-input');
  var responseInput = document.getElementById('response-input');

  caseIdField.value = '';
  emailInput.value = '';
  issueInput.value = '';
  severityInput.value = '';
  responseInput.value = '';

  // Clear all field error messages
  var errorFields = ['email-error', 'issue-error', 'severity-error', 'response-error'];
  errorFields.forEach(function (id) {
    var el = document.getElementById(id);
    if (el) {
      el.textContent = '';
    }
  });
}

/**
 * Displays a message in the message area and announces it to screen readers.
 * Success messages auto-dismiss after 5 seconds.
 * @param {string} text - Message text
 * @param {string} type - Message type: "success" or "error"
 */
function showMessage(text, type) {
  var messageArea = document.getElementById('message-area');
  var announcements = document.getElementById('announcements');

  // Create message element
  var msgDiv = document.createElement('div');
  msgDiv.className = 'message message-' + type;
  msgDiv.textContent = text;

  messageArea.appendChild(msgDiv);

  // Announce to screen readers
  announcements.textContent = text;

  // Auto-dismiss success messages after 5 seconds
  if (type === 'success') {
    setTimeout(function () {
      if (msgDiv.parentNode) {
        msgDiv.parentNode.removeChild(msgDiv);
      }
    }, 5000);
  }
}

/**
 * Shows the loading indicator.
 */
function showLoading() {
  var indicator = document.getElementById('loading-indicator');
  indicator.hidden = false;
}

/**
 * Hides the loading indicator.
 */
function hideLoading() {
  var indicator = document.getElementById('loading-indicator');
  indicator.hidden = true;
}

/**
 * Sets the disabled state of the submit button.
 * @param {boolean} disabled - Whether the button should be disabled
 */
function setSubmitDisabled(disabled) {
  var submitBtn = document.getElementById('submit-case-button');
  submitBtn.disabled = disabled;
}

/**
 * Sets the disabled state of a delete button for a specific case.
 * @param {string} caseId - The case_id whose delete button to target
 * @param {boolean} disabled - Whether the button should be disabled
 */
function setDeleteDisabled(caseId, disabled) {
  var deleteBtn = document.querySelector('.delete-button[data-case-id="' + caseId + '"]');
  if (deleteBtn) {
    deleteBtn.disabled = disabled;
  }
}

/**
 * Shows the connectivity error banner and wires the retry button.
 * @param {function} retryCallback - Function to call when retry is clicked
 */
function showConnectivityError(retryCallback) {
  var banner = document.getElementById('connectivity-error');
  var retryBtn = document.getElementById('retry-button');

  banner.hidden = false;

  // Remove any existing listener by replacing the button with a clone
  var newRetryBtn = retryBtn.cloneNode(true);
  retryBtn.parentNode.replaceChild(newRetryBtn, retryBtn);

  newRetryBtn.addEventListener('click', function () {
    if (typeof retryCallback === 'function') {
      retryCallback();
    }
  });
}

/**
 * Hides the connectivity error banner.
 */
function hideConnectivityError() {
  var banner = document.getElementById('connectivity-error');
  banner.hidden = true;
}

/**
 * Shows inline validation errors adjacent to form fields.
 * @param {Record<string, string>} errors - Object mapping field names to error messages
 */
function showValidationErrors(errors) {
  // Clear existing errors first
  var errorFields = ['email-error', 'issue-error', 'severity-error', 'response-error'];
  errorFields.forEach(function (id) {
    var el = document.getElementById(id);
    if (el) {
      el.textContent = '';
    }
  });

  // Set new error messages
  if (errors) {
    Object.keys(errors).forEach(function (key) {
      var errorSpan = document.getElementById(key + '-error');
      if (errorSpan) {
        errorSpan.textContent = errors[key];
      }
    });
  }
}

// Export for Node.js while also working as browser globals
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    renderCaseList: renderCaseList,
    renderEmptyState: renderEmptyState,
    showCreateForm: showCreateForm,
    showEditForm: showEditForm,
    clearForm: clearForm,
    showMessage: showMessage,
    showLoading: showLoading,
    hideLoading: hideLoading,
    setSubmitDisabled: setSubmitDisabled,
    setDeleteDisabled: setDeleteDisabled,
    showConnectivityError: showConnectivityError,
    hideConnectivityError: hideConnectivityError,
    showValidationErrors: showValidationErrors,
    isColumnVisible: isColumnVisible
  };
}

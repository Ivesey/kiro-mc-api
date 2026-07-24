/**
 * DOM rendering functions for the Cases Web UI.
 * Handles all visual updates: list rendering, form management, messages,
 * loading states, and focus management.
 */

/**
 * Renders the case list into #case-list.
 * Creates one div[role="listitem"] per case with case details and action buttons.
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

  cases.forEach(function (caseItem) {
    var item = document.createElement('div');
    item.setAttribute('role', 'listitem');
    item.className = 'case-item';

    var caseId = document.createElement('span');
    caseId.className = 'case-id';
    caseId.textContent = caseItem.case_id;

    var email = document.createElement('span');
    email.className = 'case-email';
    email.textContent = caseItem.email;

    var issue = document.createElement('span');
    issue.className = 'case-issue';
    issue.textContent = truncateText(caseItem.issue || '', 50);

    var severityBadge = document.createElement('span');
    severityBadge.className = 'severity-badge severity-' + caseItem.severity;
    severityBadge.textContent = caseItem.severity;

    var response = document.createElement('span');
    response.className = 'case-response';
    response.textContent = truncateText(caseItem.response || '', 50);

    var actions = document.createElement('span');
    actions.className = 'case-actions';

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

    actions.appendChild(editBtn);
    actions.appendChild(deleteBtn);

    item.appendChild(caseId);
    item.appendChild(email);
    item.appendChild(issue);
    item.appendChild(severityBadge);
    item.appendChild(response);
    item.appendChild(actions);

    caseList.appendChild(item);
  });
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
    showValidationErrors: showValidationErrors
  };
}

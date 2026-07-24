/**
 * Application controller for the Cases Web UI.
 * Handles initialization, event wiring, and orchestration between
 * validation, API, and UI modules.
 */

var _currentCases = [];

/**
 * Loads all cases from the API and renders them.
 * Shows loading indicator, handles errors with connectivity banner.
 */
async function loadCases() {
  showLoading();
  var result = await getAllCases();
  hideLoading();

  if (result.ok) {
    hideConnectivityError();
    _currentCases = result.data || [];
    if (_currentCases.length === 0) {
      renderEmptyState();
    } else {
      renderCaseList(_currentCases);
    }
  } else {
    showMessage(result.error || 'Failed to load cases', 'error');
    showConnectivityError(loadCases);
  }
}

/**
 * Handles the settings form — validates URL, persists to localStorage,
 * updates the API module base URL, and reloads cases.
 */
function handleSaveUrl() {
  var input = document.getElementById('api-url-input');
  var errorSpan = document.getElementById('api-url-error');
  var url = input.value.trim();

  var validation = validateApiUrl(url);
  if (!validation.valid) {
    errorSpan.textContent = validation.error;
    return;
  }

  errorSpan.textContent = '';
  localStorage.setItem('cases_webui_api_url', url);
  setApiBaseUrl(url);
  showMessage('API URL saved successfully', 'success');
  loadCases();
}

/**
 * Handles the case form submission for both create and edit modes.
 * Validates input, calls the appropriate API function, shows feedback.
 * @param {Event} event - The form submit event
 */
async function handleFormSubmit(event) {
  event.preventDefault();

  var caseIdField = document.getElementById('case-id-field');
  var emailInput = document.getElementById('email-input');
  var issueInput = document.getElementById('issue-input');
  var severityInput = document.getElementById('severity-input');
  var responseInput = document.getElementById('response-input');

  var formData = {
    email: emailInput.value.trim(),
    issue: issueInput.value,
    severity: severityInput.value,
    response: responseInput.value
  };

  var validation = validateCaseForm(formData);
  if (!validation.valid) {
    showValidationErrors(validation.errors);
    return;
  }

  var caseId = caseIdField.value;
  var isEdit = caseId.length > 0;

  setSubmitDisabled(true);

  var result;
  if (isEdit) {
    result = await updateCase(caseId, formData);
  } else {
    result = await createCase(formData);
  }

  setSubmitDisabled(false);

  if (result.ok) {
    hideConnectivityError();
    var action = isEdit ? 'updated' : 'created';
    showMessage('Case ' + action + ' successfully', 'success');
    var formSection = document.getElementById('case-form-section');
    formSection.hidden = true;
    await loadCases();
    var caseListSection = document.getElementById('case-list-section');
    caseListSection.focus();
  } else {
    // Check for connectivity error (no status means network failure)
    if (!result.status) {
      showConnectivityError(function () {
        handleFormSubmit(event);
      });
      showMessage(result.error || 'Network error', 'error');
    } else if (result.status === 404) {
      showMessage('Case not found — it may have been deleted', 'error');
      await loadCases();
    } else if (result.status === 400 || result.status === 422) {
      showMessage(result.error || 'Validation error from API', 'error');
    } else {
      showMessage(result.error || 'An unexpected error occurred', 'error');
    }
  }
}

/**
 * Handles clicks on delete buttons using event delegation.
 * Shows confirmation dialog, calls deleteCase, handles response.
 * @param {string} caseId - The case_id to delete
 */
async function handleDelete(caseId) {
  var confirmed = confirm('Are you sure you want to delete case ' + caseId + '?');
  if (!confirmed) {
    return;
  }

  setDeleteDisabled(caseId, true);

  var result = await deleteCase(caseId);

  setDeleteDisabled(caseId, false);

  if (result.ok) {
    hideConnectivityError();
    showMessage('Case deleted successfully', 'success');
    await loadCases();
    var caseListSection = document.getElementById('case-list-section');
    caseListSection.focus();
  } else {
    if (!result.status) {
      showConnectivityError(loadCases);
      showMessage(result.error || 'Network error', 'error');
    } else if (result.status === 404) {
      showMessage('Case not found — it may have already been deleted', 'error');
      await loadCases();
    } else {
      showMessage(result.error || 'Failed to delete case', 'error');
    }
  }
}

/**
 * Handles clicks on edit buttons using event delegation.
 * Finds the case data and shows the edit form.
 * @param {string} caseId - The case_id to edit
 */
function handleEdit(caseId) {
  var caseData = null;
  for (var i = 0; i < _currentCases.length; i++) {
    if (_currentCases[i].case_id === caseId) {
      caseData = _currentCases[i];
      break;
    }
  }
  if (caseData) {
    showEditForm(caseData);
  }
}

/**
 * Initializes the application.
 * Reads API URL from localStorage, sets up event listeners, loads cases.
 */
function init() {
  // Read API URL from localStorage or use default
  var storedUrl = localStorage.getItem('cases_webui_api_url');
  var apiUrl = storedUrl || 'http://localhost:8000';
  setApiBaseUrl(apiUrl);

  // Set the URL input to current value
  var apiUrlInput = document.getElementById('api-url-input');
  apiUrlInput.value = apiUrl;

  // Wire settings form
  var saveUrlButton = document.getElementById('save-url-button');
  saveUrlButton.addEventListener('click', handleSaveUrl);

  // Wire case form submit
  var caseForm = document.getElementById('case-form');
  caseForm.addEventListener('submit', handleFormSubmit);

  // Wire cancel button
  var cancelButton = document.getElementById('cancel-button');
  cancelButton.addEventListener('click', function () {
    var formSection = document.getElementById('case-form-section');
    formSection.hidden = true;
    var caseListSection = document.getElementById('case-list-section');
    caseListSection.focus();
  });

  // Wire new case button
  var newCaseButton = document.getElementById('new-case-button');
  newCaseButton.addEventListener('click', function () {
    showCreateForm();
  });

  // Wire refresh button
  var refreshButton = document.getElementById('refresh-button');
  refreshButton.addEventListener('click', function () {
    loadCases();
  });

  // Wire case list event delegation for edit and delete buttons
  var caseList = document.getElementById('case-list');
  caseList.addEventListener('click', function (event) {
    var target = event.target;

    if (target.classList.contains('delete-button')) {
      var caseId = target.getAttribute('data-case-id');
      if (caseId) {
        handleDelete(caseId);
      }
    } else if (target.classList.contains('edit-button')) {
      var caseId = target.getAttribute('data-case-id');
      if (caseId) {
        handleEdit(caseId);
      }
    }
  });

  // Load initial case list
  loadCases();
}

// Start the application on DOMContentLoaded
document.addEventListener('DOMContentLoaded', init);

// Export for Node.js while also working as browser globals
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { init };
}

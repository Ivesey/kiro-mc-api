/**
 * HTTP client for the Cases REST API.
 * All functions return a uniform shape: {ok, data?, error?, status?}
 * Uses AbortController for 10-second timeout on all requests.
 */

var _apiBaseUrl = '';

/**
 * Sets the API base URL used for all subsequent requests.
 * @param {string} url - Base URL (e.g., "http://localhost:8000")
 */
function setApiBaseUrl(url) {
  _apiBaseUrl = url;
}

/**
 * Formats an error message that includes the HTTP status code.
 * @param {number} status - HTTP status code
 * @param {string} [text] - Optional error text from the response
 * @returns {string}
 */
function formatErrorMessage(status, text) {
  if (text) {
    return 'HTTP error ' + status + ': ' + text;
  }
  return 'HTTP error ' + status;
}

/**
 * Fetches all cases from GET /cases/.
 * @returns {Promise<{ok: boolean, data?: Array, error?: string, status?: number}>}
 */
async function getAllCases() {
  var controller = new AbortController();
  var timeoutId = setTimeout(function () { controller.abort(); }, 10000);

  try {
    var response = await fetch(_apiBaseUrl + '/cases/', {
      method: 'GET',
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      var data = await response.json();
      return { ok: true, data: data, status: response.status };
    } else {
      var errorText = '';
      try { errorText = await response.text(); } catch (e) { /* ignore */ }
      return { ok: false, error: formatErrorMessage(response.status, errorText), status: response.status };
    }
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      return { ok: false, error: 'Request timed out after 10 seconds' };
    }
    return { ok: false, error: error.name + ': ' + error.message };
  }
}

/**
 * Creates a new case via POST /cases/.
 * @param {{email: string, issue: string, response: string, severity: string}} caseData
 * @returns {Promise<{ok: boolean, data?: object, error?: string, status?: number}>}
 */
async function createCase(caseData) {
  var controller = new AbortController();
  var timeoutId = setTimeout(function () { controller.abort(); }, 10000);

  try {
    var response = await fetch(_apiBaseUrl + '/cases/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(caseData),
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      var data = await response.json();
      return { ok: true, data: data, status: response.status };
    } else {
      var errorText = '';
      try { errorText = await response.text(); } catch (e) { /* ignore */ }
      return { ok: false, error: formatErrorMessage(response.status, errorText), status: response.status };
    }
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      return { ok: false, error: 'Request timed out after 10 seconds' };
    }
    return { ok: false, error: error.name + ': ' + error.message };
  }
}

/**
 * Updates an existing case via PUT /cases/{caseId}.
 * @param {string} caseId - UUID of the case to update
 * @param {{email: string, issue: string, response: string, severity: string}} caseData
 * @returns {Promise<{ok: boolean, data?: object, error?: string, status?: number}>}
 */
async function updateCase(caseId, caseData) {
  var controller = new AbortController();
  var timeoutId = setTimeout(function () { controller.abort(); }, 10000);

  try {
    var response = await fetch(_apiBaseUrl + '/cases/' + caseId, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(caseData),
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      var data = await response.json();
      return { ok: true, data: data, status: response.status };
    } else {
      var errorText = '';
      try { errorText = await response.text(); } catch (e) { /* ignore */ }
      return { ok: false, error: formatErrorMessage(response.status, errorText), status: response.status };
    }
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      return { ok: false, error: 'Request timed out after 10 seconds' };
    }
    return { ok: false, error: error.name + ': ' + error.message };
  }
}

/**
 * Deletes a case via DELETE /cases/{caseId}.
 * @param {string} caseId - UUID of the case to delete
 * @returns {Promise<{ok: boolean, error?: string, status?: number}>}
 */
async function deleteCase(caseId) {
  var controller = new AbortController();
  var timeoutId = setTimeout(function () { controller.abort(); }, 10000);

  try {
    var response = await fetch(_apiBaseUrl + '/cases/' + caseId, {
      method: 'DELETE',
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      return { ok: true, status: response.status };
    } else {
      var errorText = '';
      try { errorText = await response.text(); } catch (e) { /* ignore */ }
      return { ok: false, error: formatErrorMessage(response.status, errorText), status: response.status };
    }
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      return { ok: false, error: 'Request timed out after 10 seconds' };
    }
    return { ok: false, error: error.name + ': ' + error.message };
  }
}

// Export for Node.js while also working as browser globals
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { setApiBaseUrl, getAllCases, createCase, updateCase, deleteCase, formatErrorMessage };
}

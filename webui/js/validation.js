/**
 * Pure validation functions for the Cases Web UI.
 * No side effects, no DOM access — suitable for testing in Node.js or browser.
 */

/**
 * Validates an API base URL.
 * Accepts only http:// or https:// prefix and length <= 2048.
 * @param {string} url
 * @returns {{valid: boolean, error?: string}}
 */
function validateApiUrl(url) {
  if (typeof url !== 'string' || url.length === 0) {
    return { valid: false, error: 'URL is required' };
  }
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    return { valid: false, error: 'URL must start with http:// or https://' };
  }
  if (url.length > 2048) {
    return { valid: false, error: 'URL must not exceed 2048 characters' };
  }
  return { valid: true };
}

/**
 * Validates an email address.
 * Requires exactly one "@" with non-empty local and domain parts.
 * @param {string} email
 * @returns {{valid: boolean, error?: string}}
 */
function validateEmail(email) {
  if (typeof email !== 'string' || email.length === 0) {
    return { valid: false, error: 'Email is required' };
  }
  var atIndex = email.indexOf('@');
  if (atIndex === -1) {
    return { valid: false, error: 'Email must contain an @ character' };
  }
  // Check for exactly one @
  if (email.indexOf('@', atIndex + 1) !== -1) {
    return { valid: false, error: 'Email must contain exactly one @ character' };
  }
  var local = email.substring(0, atIndex);
  var domain = email.substring(atIndex + 1);
  if (local.length === 0) {
    return { valid: false, error: 'Email local part (before @) must not be empty' };
  }
  if (domain.length === 0) {
    return { valid: false, error: 'Email domain part (after @) must not be empty' };
  }
  return { valid: true };
}

/**
 * Validates the full case form data.
 * @param {{email: string, issue: string, severity: string, response?: string}} data
 * @returns {{valid: boolean, errors: Record<string, string>}}
 */
function validateCaseForm(data) {
  var errors = {};
  var allowedSeverities = ['low', 'medium', 'high', 'critical'];

  // Check required fields
  if (!data || typeof data.email !== 'string' || data.email.trim().length === 0) {
    errors.email = 'Email is required';
  } else {
    var emailResult = validateEmail(data.email);
    if (!emailResult.valid) {
      errors.email = emailResult.error;
    }
  }

  if (!data || typeof data.issue !== 'string' || data.issue.trim().length === 0) {
    errors.issue = 'Issue description is required';
  } else if (data.issue.length < 1 || data.issue.length > 2000) {
    errors.issue = 'Issue must be between 1 and 2000 characters';
  }

  if (!data || typeof data.severity !== 'string' || data.severity.trim().length === 0) {
    errors.severity = 'Severity is required';
  } else if (allowedSeverities.indexOf(data.severity) === -1) {
    errors.severity = 'Severity must be one of: low, medium, high, critical';
  }

  // Optional response field — validate length if present
  if (data && typeof data.response === 'string' && data.response.length > 5000) {
    errors.response = 'Response must not exceed 5000 characters';
  }

  var valid = Object.keys(errors).length === 0;
  return { valid: valid, errors: errors };
}

/**
 * Truncates a string to maxLen characters, appending "..." if truncated.
 * @param {string} text
 * @param {number} maxLen
 * @returns {string}
 */
function truncateText(text, maxLen) {
  if (typeof text !== 'string') {
    return '';
  }
  if (text.length <= maxLen) {
    return text;
  }
  return text.substring(0, maxLen) + '...';
}

// Export for Node.js while also working as browser globals
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { validateApiUrl, validateEmail, validateCaseForm, truncateText };
}

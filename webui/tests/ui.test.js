const fc = require('fast-check');
const { test } = require('node:test');
const assert = require('node:assert');

/**
 * Feature: cases-webui, Property 7: Form population preserves case data
 * Validates: Requirements 5.1
 *
 * For any valid Case object, populating the edit form with that case's data
 * and reading the field values back SHALL produce values identical to the
 * original case's email, issue, response, and severity fields.
 */

// --- DOM mock setup ---

function createMockElements() {
  const elements = {};

  function makeMockElement(id) {
    return {
      value: '',
      textContent: '',
      hidden: false,
      disabled: false,
      innerHTML: '',
      focus: function () {},
      className: '',
      setAttribute: function () {},
      appendChild: function () {},
    };
  }

  // All elements that ui.js accesses via getElementById
  const ids = [
    'case-form-section',
    'case-form-heading',
    'submit-case-button',
    'case-id-field',
    'email-input',
    'issue-input',
    'severity-input',
    'response-input',
    'email-error',
    'issue-error',
    'severity-error',
    'response-error',
    'case-list',
    'empty-state',
    'message-area',
    'announcements',
    'loading-indicator',
    'connectivity-error',
    'retry-button',
  ];

  ids.forEach(function (id) {
    elements[id] = makeMockElement(id);
  });

  return elements;
}

function setupGlobalDom() {
  const elements = createMockElements();

  global.document = {
    getElementById: function (id) {
      return elements[id] || { value: '', textContent: '', hidden: false, disabled: false, focus: function () {} };
    },
    createElement: function () {
      return {
        value: '',
        textContent: '',
        hidden: false,
        className: '',
        setAttribute: function () {},
        appendChild: function () {},
        addEventListener: function () {},
        cloneNode: function () { return this; },
        parentNode: { replaceChild: function () {} },
      };
    },
    querySelector: function () { return null; },
  };

  return elements;
}

// Set up global DOM mock before requiring ui.js
const mockElements = setupGlobalDom();

// Set up truncateText as global (ui.js uses it as a browser global)
const { truncateText } = require('../js/validation');
global.truncateText = truncateText;

// Now require ui.js which will use the mocked globals
const { showEditForm } = require('../js/ui');

// --- Generators ---

// UUID-like string generator
const uuidArb = fc.tuple(
  fc.hexaString({ minLength: 8, maxLength: 8 }),
  fc.hexaString({ minLength: 4, maxLength: 4 }),
  fc.hexaString({ minLength: 4, maxLength: 4 }),
  fc.hexaString({ minLength: 4, maxLength: 4 }),
  fc.hexaString({ minLength: 12, maxLength: 12 })
).map(([a, b, c, d, e]) => `${a}-${b}-${c}-${d}-${e}`);

// Valid email generator: non-empty local @ non-empty domain
const emailArb = fc.tuple(
  fc.stringOf(fc.constantFrom(...'abcdefghijklmnopqrstuvwxyz0123456789._%+-'.split('')), { minLength: 1, maxLength: 64 }),
  fc.stringOf(fc.constantFrom(...'abcdefghijklmnopqrstuvwxyz0123456789.-'.split('')), { minLength: 1, maxLength: 50 }),
  fc.constantFrom('.com', '.org', '.net', '.io', '.dev')
).map(([local, domain, tld]) => `${local}@${domain}${tld}`);

// Issue text: 1-2000 printable chars
const issueArb = fc.string({ minLength: 1, maxLength: 2000 });

// Severity: one of the allowed values
const severityArb = fc.constantFrom('low', 'medium', 'high', 'critical');

// Response: 0-5000 chars (can be empty string)
const responseArb = fc.string({ minLength: 0, maxLength: 500 });

// Full Case object arbitrary
const caseArb = fc.record({
  case_id: uuidArb,
  email: emailArb,
  issue: issueArb,
  severity: severityArb,
  response: responseArb,
});

// --- Property test ---

test('Feature: cases-webui, Property 7: Form population preserves case data', () => {
  fc.assert(
    fc.property(caseArb, (caseData) => {
      // Reset mock element values before each iteration
      mockElements['case-id-field'].value = '';
      mockElements['email-input'].value = '';
      mockElements['issue-input'].value = '';
      mockElements['severity-input'].value = '';
      mockElements['response-input'].value = '';
      mockElements['email-error'].textContent = '';
      mockElements['issue-error'].textContent = '';
      mockElements['severity-error'].textContent = '';
      mockElements['response-error'].textContent = '';

      // Populate the form
      showEditForm(caseData);

      // Read values back and verify equality
      assert.strictEqual(
        mockElements['case-id-field'].value,
        caseData.case_id,
        `case_id mismatch: expected "${caseData.case_id}", got "${mockElements['case-id-field'].value}"`
      );
      assert.strictEqual(
        mockElements['email-input'].value,
        caseData.email,
        `email mismatch: expected "${caseData.email}", got "${mockElements['email-input'].value}"`
      );
      assert.strictEqual(
        mockElements['issue-input'].value,
        caseData.issue,
        `issue mismatch: expected "${caseData.issue}", got "${mockElements['issue-input'].value}"`
      );
      assert.strictEqual(
        mockElements['severity-input'].value,
        caseData.severity,
        `severity mismatch: expected "${caseData.severity}", got "${mockElements['severity-input'].value}"`
      );
      assert.strictEqual(
        mockElements['response-input'].value,
        caseData.response,
        `response mismatch: expected "${caseData.response}", got "${mockElements['response-input'].value}"`
      );
    }),
    { numRuns: 100 }
  );
});

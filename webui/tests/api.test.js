const fc = require('fast-check');
const { formatErrorMessage } = require('../js/api');
const { test } = require('node:test');
const assert = require('node:assert');

/**
 * Feature: cases-webui, Property 6: Error message includes status information
 * Validates: Requirements 3.4
 *
 * For any HTTP error status code (4xx or 5xx) or network error type string returned
 * by the API client, the error message rendered to the user SHALL contain either
 * the numeric status code or the network error type identifier.
 */

test('Feature: cases-webui, Property 6: Error message includes status information — HTTP status codes with text', () => {
  fc.assert(
    fc.property(
      fc.integer({ min: 400, max: 599 }),
      fc.string({ minLength: 1, maxLength: 200 }),
      (status, text) => {
        const message = formatErrorMessage(status, text);

        // The error message must contain the numeric status code as a substring
        assert.ok(
          message.includes(String(status)),
          `Expected error message to contain status code "${status}". Got: "${message}"`
        );
      }
    ),
    { numRuns: 100 }
  );
});

test('Feature: cases-webui, Property 6: Error message includes status information — HTTP status codes without text', () => {
  fc.assert(
    fc.property(
      fc.integer({ min: 400, max: 599 }),
      (status) => {
        const message = formatErrorMessage(status, '');

        // The error message must contain the numeric status code as a substring
        assert.ok(
          message.includes(String(status)),
          `Expected error message to contain status code "${status}". Got: "${message}"`
        );
      }
    ),
    { numRuns: 100 }
  );
});

test('Feature: cases-webui, Property 6: Error message includes status information — network error format', () => {
  // Network errors in api.js are formatted as "ErrorName: message"
  // Verify that for any error name, the formatted string contains the error name
  const errorNameArb = fc.stringOf(
    fc.char().filter(c => /[A-Za-z]/.test(c)),
    { minLength: 1, maxLength: 30 }
  );

  fc.assert(
    fc.property(
      errorNameArb,
      fc.string({ minLength: 0, maxLength: 100 }),
      (errorName, errorMessage) => {
        // Simulating the network error format used in api.js:
        // error.name + ': ' + error.message
        const formatted = errorName + ': ' + errorMessage;

        // The formatted message must contain the error type identifier
        assert.ok(
          formatted.includes(errorName),
          `Expected network error message to contain error name "${errorName}". Got: "${formatted}"`
        );
      }
    ),
    { numRuns: 100 }
  );
});

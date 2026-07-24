const fc = require('fast-check');
const { validateApiUrl, truncateText, validateEmail, validateCaseForm } = require('../js/validation');
const { test } = require('node:test');
const assert = require('node:assert');

/**
 * Feature: cases-webui, Property 1: API URL validation correctness
 * Validates: Requirements 2.1, 2.5
 *
 * For any string, validateApiUrl SHALL return {valid: true} if and only if
 * the string begins with "http://" or "https://" and has length <= 2048 characters.
 * For all other strings, it SHALL return {valid: false} with an error message.
 */
test('Feature: cases-webui, Property 1: API URL validation correctness', () => {
  // Helper: determine expected validity based on the specification rules
  function shouldBeValid(s) {
    if (typeof s !== 'string' || s.length === 0) return false;
    if (!s.startsWith('http://') && !s.startsWith('https://')) return false;
    if (s.length > 2048) return false;
    return true;
  }

  fc.assert(
    fc.property(
      fc.oneof(
        // Arbitrary strings (may or may not satisfy the rules)
        fc.string({ minLength: 0, maxLength: 100 }),
        // Valid http:// URLs of varying length
        fc.string({ minLength: 0, maxLength: 200 }).map(s => 'http://' + s.replace(/[\x00-\x1f]/g, '')),
        // Valid https:// URLs of varying length
        fc.string({ minLength: 0, maxLength: 200 }).map(s => 'https://' + s.replace(/[\x00-\x1f]/g, '')),
        // URLs that exceed 2048 characters (should be invalid)
        fc.string({ minLength: 2042, maxLength: 2100 }).map(s => 'http://' + s),
        // Strings with wrong protocol prefixes
        fc.constantFrom('ftp://', 'ws://', 'file://', 'HTTP://', 'HTTPS://').chain(
          prefix => fc.string({ minLength: 0, maxLength: 50 }).map(s => prefix + s)
        ),
        // Empty string
        fc.constant('')
      ),
      (input) => {
        const result = validateApiUrl(input);
        const expectedValid = shouldBeValid(input);

        if (expectedValid) {
          assert.strictEqual(result.valid, true,
            `Expected valid=true for "${input}" (starts with http:// or https://, length=${input.length} <= 2048)`);
          assert.strictEqual(result.error, undefined,
            `Expected no error for valid URL "${input}"`);
        } else {
          assert.strictEqual(result.valid, false,
            `Expected valid=false for "${input}" (does not meet protocol prefix + length rules)`);
          assert.ok(typeof result.error === 'string' && result.error.length > 0,
            `Expected an error message for invalid URL "${input}"`);
        }
      }
    ),
    { numRuns: 100 }
  );
});

/**
 * Feature: cases-webui, Property 3: Text truncation correctness
 * Validates: Requirements 3.2
 *
 * For any string and positive integer maxLen:
 * - If the string's length <= maxLen, truncateText returns the original string unchanged.
 * - If the string's length > maxLen, truncateText returns a string of exactly maxLen + 3 characters
 *   whose first maxLen characters equal the input's first maxLen characters, followed by "...".
 */
test('Feature: cases-webui, Property 3: Text truncation correctness', () => {
  fc.assert(
    fc.property(
      fc.string(),
      fc.integer({ min: 1, max: 1000 }),
      (text, maxLen) => {
        const result = truncateText(text, maxLen);

        if (text.length <= maxLen) {
          // Short strings are returned unchanged
          assert.strictEqual(result, text,
            `Expected short string to be unchanged. text.length=${text.length}, maxLen=${maxLen}`);
        } else {
          // Long strings are truncated to maxLen chars + "..."
          assert.strictEqual(result.length, maxLen + 3,
            `Expected truncated length to be maxLen + 3. Got ${result.length}, expected ${maxLen + 3}`);

          // First maxLen characters of result equal first maxLen characters of input
          assert.strictEqual(result.substring(0, maxLen), text.substring(0, maxLen),
            'Expected first maxLen characters to match input');

          // Result ends with "..." when truncation occurs
          assert.strictEqual(result.slice(-3), '...',
            'Expected truncated string to end with "..."');
        }
      }
    ),
    { numRuns: 100 }
  );
});

/**
 * Feature: cases-webui, Property 2: Email validation correctness
 * Validates: Requirements 4.7
 *
 * For any string, validateEmail SHALL return {valid: true} if and only if
 * the string contains exactly one @ character where both the local part
 * (before @) and the domain part (after @) are non-empty.
 * For all other strings, it SHALL return {valid: false}.
 */
test('Feature: cases-webui, Property 2: Email validation correctness', () => {
  // Helper: determine expected validity based on the rule
  function shouldBeValid(s) {
    if (typeof s !== 'string' || s.length === 0) return false;
    const atCount = (s.match(/@/g) || []).length;
    if (atCount !== 1) return false;
    const atIndex = s.indexOf('@');
    const local = s.substring(0, atIndex);
    const domain = s.substring(atIndex + 1);
    return local.length > 0 && domain.length > 0;
  }

  fc.assert(
    fc.property(
      // Generate strings with varying numbers of @ characters
      fc.oneof(
        // Strings with no @ (always invalid)
        fc.string().filter(s => !s.includes('@')),
        // Strings with exactly one @ (valid iff non-empty parts)
        fc.tuple(
          fc.string({ minLength: 0, maxLength: 50 }),
          fc.string({ minLength: 0, maxLength: 50 })
        ).map(([local, domain]) => {
          // Remove any @ from local and domain to control placement
          const cleanLocal = local.replace(/@/g, '');
          const cleanDomain = domain.replace(/@/g, '');
          return cleanLocal + '@' + cleanDomain;
        }),
        // Strings with multiple @ characters (always invalid)
        fc.tuple(
          fc.string({ minLength: 0, maxLength: 20 }),
          fc.string({ minLength: 0, maxLength: 20 }),
          fc.string({ minLength: 0, maxLength: 20 })
        ).map(([a, b, c]) => {
          const cleanA = a.replace(/@/g, '');
          const cleanB = b.replace(/@/g, '');
          const cleanC = c.replace(/@/g, '');
          return cleanA + '@' + cleanB + '@' + cleanC;
        }),
        // Arbitrary strings (may have any number of @)
        fc.string({ minLength: 0, maxLength: 100 })
      ),
      (input) => {
        const result = validateEmail(input);
        const expectedValid = shouldBeValid(input);

        if (expectedValid) {
          assert.strictEqual(result.valid, true,
            `Expected valid=true for "${input}" (has exactly one @ with non-empty parts)`);
          assert.strictEqual(result.error, undefined,
            `Expected no error for valid email "${input}"`);
        } else {
          assert.strictEqual(result.valid, false,
            `Expected valid=false for "${input}" (does not meet exactly-one-@ rule)`);
          assert.ok(typeof result.error === 'string' && result.error.length > 0,
            `Expected an error message for invalid email "${input}"`);
        }
      }
    ),
    { numRuns: 100 }
  );
});

/**
 * Feature: cases-webui, Property 4: Form validation completeness
 * Validates: Requirements 4.5, 4.6, 5.2
 *
 * For any form data object where at least one of email, issue, or severity is empty or missing,
 * validateCaseForm SHALL return {valid: false} with an error keyed to each invalid/missing required field.
 * For any form data where all required fields are present and individually valid (email passes email
 * validation, severity is one of low/medium/high/critical, issue is 1-2000 chars),
 * validateCaseForm SHALL return {valid: true}.
 */

// Generator for a valid email: non-empty local part + "@" + non-empty domain part,
// with no additional "@" characters.
const validEmailArb = fc.tuple(
  fc.stringOf(fc.char().filter(c => c !== '@' && c.trim().length > 0), { minLength: 1, maxLength: 20 }),
  fc.stringOf(fc.char().filter(c => c !== '@' && c.trim().length > 0), { minLength: 1, maxLength: 20 })
).map(([local, domain]) => `${local}@${domain}`);

const validSeverityArb = fc.constantFrom('low', 'medium', 'high', 'critical');

// Generator for a valid issue string (1-2000 chars, non-empty after trim)
const validIssueArb = fc.string({ minLength: 1, maxLength: 2000 }).filter(s => s.trim().length > 0);

// Generator for a valid optional response (0-5000 chars)
const validResponseArb = fc.oneof(
  fc.constant(undefined),
  fc.string({ minLength: 0, maxLength: 5000 })
);

test('Feature: cases-webui, Property 4: Form validation completeness — valid forms accepted', () => {
  fc.assert(
    fc.property(
      validEmailArb,
      validIssueArb,
      validSeverityArb,
      validResponseArb,
      (email, issue, severity, response) => {
        const data = { email, issue, severity };
        if (response !== undefined) {
          data.response = response;
        }

        const result = validateCaseForm(data);

        assert.strictEqual(result.valid, true,
          `Expected valid form to pass. Got errors: ${JSON.stringify(result.errors)} for data: ${JSON.stringify(data)}`);
        assert.deepStrictEqual(result.errors, {},
          `Expected no errors for valid form. Got: ${JSON.stringify(result.errors)}`);
      }
    ),
    { numRuns: 100 }
  );
});

test('Feature: cases-webui, Property 4: Form validation completeness — missing/empty required fields rejected', () => {
  // Generate form data where at least one required field is missing or empty
  const missingFieldArb = fc.record({
    email: fc.oneof(
      fc.constant(undefined),   // missing
      fc.constant(''),          // empty
      validEmailArb             // valid
    ),
    issue: fc.oneof(
      fc.constant(undefined),   // missing
      fc.constant(''),          // empty
      validIssueArb             // valid
    ),
    severity: fc.oneof(
      fc.constant(undefined),   // missing
      fc.constant(''),          // empty
      validSeverityArb          // valid
    )
  }).filter(data => {
    // At least one required field must be missing or empty
    const emailMissing = data.email === undefined || data.email === '';
    const issueMissing = data.issue === undefined || data.issue === '';
    const severityMissing = data.severity === undefined || data.severity === '';
    return emailMissing || issueMissing || severityMissing;
  });

  fc.assert(
    fc.property(
      missingFieldArb,
      (data) => {
        const result = validateCaseForm(data);

        // Must be invalid
        assert.strictEqual(result.valid, false,
          `Expected invalid result when required field(s) missing. Data: ${JSON.stringify(data)}`);

        // Check that each missing/empty required field has a corresponding error
        const emailMissing = data.email === undefined || data.email === '';
        const issueMissing = data.issue === undefined || data.issue === '';
        const severityMissing = data.severity === undefined || data.severity === '';

        if (emailMissing) {
          assert.ok('email' in result.errors,
            `Expected 'email' error when email is missing/empty. Errors: ${JSON.stringify(result.errors)}`);
        }
        if (issueMissing) {
          assert.ok('issue' in result.errors,
            `Expected 'issue' error when issue is missing/empty. Errors: ${JSON.stringify(result.errors)}`);
        }
        if (severityMissing) {
          assert.ok('severity' in result.errors,
            `Expected 'severity' error when severity is missing/empty. Errors: ${JSON.stringify(result.errors)}`);
        }
      }
    ),
    { numRuns: 100 }
  );
});

test('Feature: cases-webui, Property 4: Form validation completeness — invalid severity rejected', () => {
  // Valid email and issue, but severity is not in the allowed list
  const invalidSeverityArb = fc.string({ minLength: 1, maxLength: 50 })
    .filter(s => !['low', 'medium', 'high', 'critical', ''].includes(s) && s.trim().length > 0);

  fc.assert(
    fc.property(
      validEmailArb,
      validIssueArb,
      invalidSeverityArb,
      (email, issue, severity) => {
        const data = { email, issue, severity };
        const result = validateCaseForm(data);

        assert.strictEqual(result.valid, false,
          `Expected invalid result for bad severity "${severity}"`);
        assert.ok('severity' in result.errors,
          `Expected 'severity' error for invalid value "${severity}". Errors: ${JSON.stringify(result.errors)}`);
      }
    ),
    { numRuns: 100 }
  );
});

test('Feature: cases-webui, Property 4: Form validation completeness — issue length boundary enforcement', () => {
  // Issue too long (> 2000 chars) should be rejected
  const longIssueArb = fc.string({ minLength: 2001, maxLength: 3000 });

  fc.assert(
    fc.property(
      validEmailArb,
      longIssueArb,
      validSeverityArb,
      (email, issue, severity) => {
        const data = { email, issue, severity };
        const result = validateCaseForm(data);

        assert.strictEqual(result.valid, false,
          `Expected invalid result for issue length ${issue.length}`);
        assert.ok('issue' in result.errors,
          `Expected 'issue' error for oversized issue. Errors: ${JSON.stringify(result.errors)}`);
      }
    ),
    { numRuns: 100 }
  );
});

test('Feature: cases-webui, Property 4: Form validation completeness — response length boundary enforcement', () => {
  // Response too long (> 5000 chars) should be rejected
  const longResponseArb = fc.string({ minLength: 5001, maxLength: 6000 });

  fc.assert(
    fc.property(
      validEmailArb,
      validIssueArb,
      validSeverityArb,
      longResponseArb,
      (email, issue, severity, response) => {
        const data = { email, issue, severity, response };
        const result = validateCaseForm(data);

        assert.strictEqual(result.valid, false,
          `Expected invalid result for response length ${response.length}`);
        assert.ok('response' in result.errors,
          `Expected 'response' error for oversized response. Errors: ${JSON.stringify(result.errors)}`);
      }
    ),
    { numRuns: 100 }
  );
});

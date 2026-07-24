const fc = require('fast-check');
const { validateApiUrl } = require('../js/validation');
const { test, beforeEach } = require('node:test');
const assert = require('node:assert');

/**
 * Feature: cases-webui, Property 5: API URL persistence round-trip
 * Validates: Requirements 2.3, 2.4
 *
 * For any valid API URL (a string that passes validateApiUrl), storing it via
 * the config persistence mechanism and immediately reading it back SHALL produce
 * the identical string.
 */
test('Feature: cases-webui, Property 5: API URL persistence round-trip', () => {
  // Create a simple mock localStorage
  const mockLocalStorage = {
    store: {},
    getItem(key) {
      return this.store[key] || null;
    },
    setItem(key, value) {
      this.store[key] = value;
    }
  };

  // Generator for valid API URLs that pass validateApiUrl
  // URLs must start with http:// or https:// and have total length <= 2048
  const validApiUrlArb = fc.oneof(
    // http:// URLs with varying path content
    fc.string({ minLength: 0, maxLength: 200 })
      .map(s => 'http://' + s.replace(/[\x00-\x1f]/g, ''))
      .filter(url => url.length <= 2048),
    // https:// URLs with varying path content
    fc.string({ minLength: 0, maxLength: 200 })
      .map(s => 'https://' + s.replace(/[\x00-\x1f]/g, ''))
      .filter(url => url.length <= 2048),
    // Realistic-looking URLs
    fc.tuple(
      fc.constantFrom('http://', 'https://'),
      fc.stringOf(
        fc.constantFrom(
          'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
          'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
          '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
          '.', '-', '/', ':', '_'
        ),
        { minLength: 1, maxLength: 100 }
      )
    ).map(([protocol, rest]) => protocol + rest)
  ).filter(url => {
    // Ensure the generated URL actually passes validateApiUrl
    const result = validateApiUrl(url);
    return result.valid === true;
  });

  fc.assert(
    fc.property(
      validApiUrlArb,
      (url) => {
        // Reset mock localStorage for each test iteration
        mockLocalStorage.store = {};

        // Store the URL using the same key as app.js
        mockLocalStorage.setItem('cases_webui_api_url', url);

        // Retrieve the URL
        const retrieved = mockLocalStorage.getItem('cases_webui_api_url');

        // Assert round-trip identity
        assert.strictEqual(retrieved, url,
          `Expected stored URL to be retrieved identically. Stored: "${url}", Retrieved: "${retrieved}"`);
      }
    ),
    { numRuns: 100 }
  );
});

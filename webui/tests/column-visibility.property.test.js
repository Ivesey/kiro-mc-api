const fc = require('fast-check');
const { test } = require('node:test');
const assert = require('node:assert');

/**
 * Feature: column-visibility-config, Property 1: Visible column count matches configuration
 * Validates: Requirements 3.2, 3.4
 *
 * For any valid columnVisibility configuration (an object mapping column identifiers
 * to booleans), the number of <th> elements in the rendered table header SHALL equal
 * the number of columns whose visibility resolves to true.
 */

// --- DOM mock setup (same pattern as ui.render.test.js) ---

function createMockDOM() {
  function makeMockElement(tagName) {
    const el = {
      tagName: tagName.toUpperCase(),
      className: '',
      textContent: '',
      hidden: false,
      disabled: false,
      value: '',
      children: [],
      attributes: {},
      parentNode: null,
      type: '',
      setAttribute: function (name, value) {
        el.attributes[name] = value;
      },
      getAttribute: function (name) {
        return el.attributes[name] || null;
      },
      appendChild: function (child) {
        child.parentNode = el;
        el.children.push(child);
        return child;
      },
      removeChild: function (child) {
        const idx = el.children.indexOf(child);
        if (idx !== -1) el.children.splice(idx, 1);
        return child;
      },
      cloneNode: function () { return makeMockElement(tagName); },
      addEventListener: function () {},
      focus: function () {},
      querySelector: function () { return null; },
    };
    Object.defineProperty(el, 'innerHTML', {
      get: function () { return el._innerHTML || ''; },
      set: function (val) {
        el._innerHTML = val;
        if (val === '') {
          el.children = [];
        }
      },
      enumerable: true,
      configurable: true,
    });
    return el;
  }

  const elements = {};
  const ids = [
    'case-list',
    'empty-state',
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
    'message-area',
    'announcements',
    'loading-indicator',
    'connectivity-error',
    'retry-button',
  ];

  ids.forEach(function (id) {
    elements[id] = makeMockElement('div');
  });

  global.document = {
    getElementById: function (id) {
      return elements[id] || makeMockElement('div');
    },
    createElement: function (tagName) {
      return makeMockElement(tagName);
    },
    querySelector: function () { return null; },
  };

  return elements;
}

// Set up mock DOM
const mockElements = createMockDOM();

// Set up truncateText as global (ui.js uses it as a browser global)
const { truncateText } = require('../js/validation');
global.truncateText = truncateText;

// Now require ui.js which will use the mocked globals
const { renderCaseList } = require('../js/ui');

// --- Generators ---

// The 6 valid column identifiers
const COLUMN_IDS = ['caseId', 'email', 'issue', 'severity', 'response', 'actions'];

// Generator for a columnVisibility config: each of the 6 columns randomly true or false
const columnVisibilityArb = fc.record({
  caseId: fc.boolean(),
  email: fc.boolean(),
  issue: fc.boolean(),
  severity: fc.boolean(),
  response: fc.boolean(),
  actions: fc.boolean(),
});

// UUID-like string generator
const uuidArb = fc.tuple(
  fc.hexaString({ minLength: 8, maxLength: 8 }),
  fc.hexaString({ minLength: 4, maxLength: 4 }),
  fc.hexaString({ minLength: 4, maxLength: 4 }),
  fc.hexaString({ minLength: 4, maxLength: 4 }),
  fc.hexaString({ minLength: 12, maxLength: 12 })
).map(([a, b, c, d, e]) => `${a}-${b}-${c}-${d}-${e}`);

// Valid email generator
const emailArb = fc.tuple(
  fc.stringOf(fc.constantFrom(...'abcdefghijklmnopqrstuvwxyz0123456789'.split('')), { minLength: 1, maxLength: 10 }),
  fc.stringOf(fc.constantFrom(...'abcdefghijklmnopqrstuvwxyz'.split('')), { minLength: 1, maxLength: 5 }),
  fc.constantFrom('.com', '.org', '.net')
).map(([local, domain, tld]) => `${local}@${domain}${tld}`);

// Severity
const severityArb = fc.constantFrom('low', 'medium', 'high', 'critical');

// Full Case object arbitrary
const caseArb = fc.record({
  case_id: uuidArb,
  email: emailArb,
  issue: fc.string({ minLength: 1, maxLength: 100 }),
  severity: severityArb,
  response: fc.string({ minLength: 0, maxLength: 100 }),
});

// Non-empty array of cases
const casesArb = fc.array(caseArb, { minLength: 1, maxLength: 5 });

// --- Helper: walk the DOM tree to find elements by tagName ---

function findAllByTag(root, tagName) {
  const results = [];
  const upperTag = tagName.toUpperCase();
  function walk(node) {
    if (node.tagName === upperTag) {
      results.push(node);
    }
    if (node.children) {
      node.children.forEach(walk);
    }
  }
  walk(root);
  return results;
}

// --- Property-based test ---

test('Feature: column-visibility-config, Property 1: Visible column count matches configuration', () => {
  /**
   * Validates: Requirements 3.2, 3.4
   *
   * For any random columnVisibility config, the number of <th> elements in the
   * rendered table equals the number of columns whose visibility resolves to true.
   */
  fc.assert(
    fc.property(
      columnVisibilityArb,
      casesArb,
      (visibilityConfig, cases) => {
        // Set global AppConfig before rendering
        global.AppConfig = { columnVisibility: visibilityConfig };

        // Reset the container
        const caseList = mockElements['case-list'];
        caseList.children = [];
        caseList.hidden = true;
        caseList._innerHTML = '';
        mockElements['empty-state'].hidden = false;

        // Call the function under test
        renderCaseList(cases);

        // Count expected visible columns (those set to true)
        const expectedVisibleCount = COLUMN_IDS.filter(function (id) {
          return visibilityConfig[id] === true;
        }).length;

        // Find <th> elements in the rendered output
        const thElements = findAllByTag(caseList, 'TH');

        assert.strictEqual(
          thElements.length,
          expectedVisibleCount,
          'Expected ' + expectedVisibleCount + ' <th> elements for config ' +
          JSON.stringify(visibilityConfig) + ', but got ' + thElements.length
        );

        // Cleanup
        delete global.AppConfig;
      }
    ),
    { numRuns: 100 }
  );
});

// --- Property 2: Hidden columns produce no cells ---

/**
 * Feature: column-visibility-config, Property 2: Hidden columns produce no cells
 * Validates: Requirements 3.2, 3.3
 *
 * For any column identifier set to `false` in `columnVisibility`, and for any
 * non-empty array of cases, the rendered table SHALL contain zero header cells
 * and zero data cells for that column.
 */

// Column identifier to header text and cell class mapping
const COLUMN_MAP = {
  caseId: { header: 'Case ID', cellClass: null },
  email: { header: 'Email', cellClass: null },
  issue: { header: 'Issue', cellClass: 'case-issue' },
  severity: { header: 'Severity', cellClass: null },
  response: { header: 'Response', cellClass: 'case-response' },
  actions: { header: 'Actions', cellClass: 'actions' },
};

// Generator for a columnVisibility config where at least one column is false
const configWithHiddenColumnsArb = fc.record({
  caseId: fc.boolean(),
  email: fc.boolean(),
  issue: fc.boolean(),
  severity: fc.boolean(),
  response: fc.boolean(),
  actions: fc.boolean(),
}).filter(function (config) {
  return Object.values(config).some(function (v) { return v === false; });
});

// Helper: find all elements by className (partial match)
function findAllByClass(root, className) {
  const results = [];
  function walk(node) {
    if (node.className && node.className.indexOf(className) !== -1) {
      results.push(node);
    }
    if (node.children) {
      node.children.forEach(walk);
    }
  }
  walk(root);
  return results;
}

test('Feature: column-visibility-config, Property 2: Hidden columns produce no cells', () => {
  /**
   * Validates: Requirements 3.2, 3.3
   *
   * For any column identifier set to `false` in `columnVisibility`, and for any
   * non-empty array of cases, the rendered table SHALL contain zero header cells
   * and zero data cells for that column.
   */
  fc.assert(
    fc.property(configWithHiddenColumnsArb, casesArb, (config, cases) => {
      // Set the global AppConfig
      global.AppConfig = { columnVisibility: config };

      // Reset the container
      const caseList = mockElements['case-list'];
      caseList.children = [];
      caseList.hidden = true;
      caseList._innerHTML = '';
      mockElements['empty-state'].hidden = false;

      // Call the function under test
      renderCaseList(cases);

      // Determine which columns are hidden
      const hiddenColumnIds = COLUMN_IDS.filter(function (id) {
        return config[id] === false;
      });

      // For each hidden column, verify no header or data cells exist
      hiddenColumnIds.forEach(function (colId) {
        const colInfo = COLUMN_MAP[colId];

        // Check no <th> has the header text for this column
        const allTh = findAllByTag(caseList, 'TH');
        const matchingHeaders = allTh.filter(function (th) {
          return th.textContent === colInfo.header;
        });
        assert.strictEqual(
          matchingHeaders.length, 0,
          'Expected zero <th> with text "' + colInfo.header + '" when column "' + colId + '" is hidden, but found ' + matchingHeaders.length
        );

        // Check no data cells with identifying class exist for columns that have one
        if (colInfo.cellClass) {
          const matchingCells = findAllByClass(caseList, colInfo.cellClass);
          assert.strictEqual(
            matchingCells.length, 0,
            'Expected zero cells with class "' + colInfo.cellClass + '" when column "' + colId + '" is hidden, but found ' + matchingCells.length
          );
        }
      });

      // Clean up
      delete global.AppConfig;
    }),
    { numRuns: 100 }
  );
});

// --- Property 5: Unknown keys are ignored ---

/**
 * Feature: column-visibility-config, Property 5: Unknown keys are ignored
 * Validates: Requirements 5.2
 *
 * For any `columnVisibility` object containing extra keys (not matching any valid
 * column identifier), the rendered table SHALL behave identically to a config without
 * those extra keys — rendering all valid columns according to their own visibility flags.
 */

// Generator for extra keys that do not collide with valid COLUMN_IDS
const extraKeysArb = fc.dictionary(
  fc.string({ minLength: 1, maxLength: 10 }).filter(function (k) {
    return !COLUMN_IDS.includes(k);
  }),
  fc.anything(),
  { minKeys: 1, maxKeys: 5 }
);

test('Feature: column-visibility-config, Property 5: Unknown keys are ignored', () => {
  /**
   * Validates: Requirements 5.2
   *
   * Generate a random columnVisibility config for the 6 valid columns, merge in
   * 1-5 extra keys with random names and values, and verify that the rendered
   * table has the same number of <th> elements as a config without the extra keys.
   */
  fc.assert(
    fc.property(
      columnVisibilityArb,
      extraKeysArb,
      casesArb,
      (visibilityConfig, extraKeys, cases) => {
        // Merge extra keys into the valid config
        var mergedConfig = Object.assign({}, visibilityConfig, extraKeys);

        // Set global AppConfig with the merged config (includes unknown keys)
        global.AppConfig = { columnVisibility: mergedConfig };

        // Reset the container
        const caseList = mockElements['case-list'];
        caseList.children = [];
        caseList.hidden = true;
        caseList._innerHTML = '';
        mockElements['empty-state'].hidden = false;

        // Call the function under test
        renderCaseList(cases);

        // Count expected visible columns based ONLY on valid column flags
        const expectedVisibleCount = COLUMN_IDS.filter(function (id) {
          return visibilityConfig[id] === true;
        }).length;

        // Find <th> elements in the rendered output
        const thElements = findAllByTag(caseList, 'TH');

        assert.strictEqual(
          thElements.length,
          expectedVisibleCount,
          'Expected ' + expectedVisibleCount + ' <th> elements (extra keys should be ignored), ' +
          'but got ' + thElements.length + '. Config: ' + JSON.stringify(mergedConfig)
        );

        // Cleanup
        delete global.AppConfig;
      }
    ),
    { numRuns: 100 }
  );
});

// --- Property 4: Missing or invalid config defaults to all-visible ---

/**
 * Feature: column-visibility-config, Property 4: Missing or invalid config defaults to all-visible
 * Validates: Requirements 4.1, 4.2, 5.1
 *
 * For any non-empty array of cases, when AppConfig is undefined, or columnVisibility
 * is missing, or a column identifier is absent from columnVisibility, or a column
 * identifier maps to a non-boolean value, the rendered table SHALL contain 6 header
 * columns (the full set).
 */

// Generator for non-boolean values (strings, numbers, objects, null, undefined)
const nonBooleanArb = fc.oneof(
  fc.string(),
  fc.integer(),
  fc.float(),
  fc.constant(null),
  fc.constant(undefined),
  fc.constant('true'),
  fc.constant('false'),
  fc.constant(0),
  fc.constant(1),
  fc.record({ nested: fc.boolean() })
);

// Scenario 1: AppConfig is undefined
const scenarioUndefinedAppConfig = fc.constant({ type: 'undefinedAppConfig' });

// Scenario 2: columnVisibility is missing from AppConfig
const scenarioMissingColumnVisibility = fc.oneof(
  fc.constant({ type: 'emptyAppConfig', value: {} }),
  fc.record({
    type: fc.constant('appConfigNoVisibility'),
    value: fc.record({ somethingElse: fc.string() })
  })
);

// Scenario 3: Some column identifiers absent from config (remaining are all true)
const scenarioAbsentKeys = fc.subarray(COLUMN_IDS, { minLength: 1, maxLength: 5 }).map(function (subset) {
  var config = {};
  subset.forEach(function (key) { config[key] = true; });
  return { type: 'absentKeys', value: config };
});

// Scenario 4: Some columns have non-boolean values
const scenarioNonBooleanValues = fc.tuple(
  fc.subarray(COLUMN_IDS, { minLength: 1, maxLength: 6 }),
  fc.array(nonBooleanArb, { minLength: 1, maxLength: 6 })
).map(function (pair) {
  var keys = pair[0];
  var values = pair[1];
  var config = {};
  keys.forEach(function (key, i) {
    config[key] = values[i % values.length];
  });
  return { type: 'nonBooleanValues', value: config };
});

// Combined scenario generator using fc.oneof
const invalidConfigScenarioArb = fc.oneof(
  scenarioUndefinedAppConfig,
  scenarioMissingColumnVisibility,
  scenarioAbsentKeys,
  scenarioNonBooleanValues
);

test('Feature: column-visibility-config, Property 4: Missing or invalid config defaults to all-visible', () => {
  /**
   * Validates: Requirements 4.1, 4.2, 5.1
   *
   * For any non-empty array of cases, when AppConfig is undefined, or columnVisibility
   * is missing, or a column identifier is absent, or values are non-boolean, the
   * rendered table SHALL contain 6 header columns (the full set).
   */
  fc.assert(
    fc.property(invalidConfigScenarioArb, casesArb, (scenario, cases) => {
      // Apply the scenario to global state
      switch (scenario.type) {
        case 'undefinedAppConfig':
          delete global.AppConfig;
          break;
        case 'emptyAppConfig':
          global.AppConfig = scenario.value;
          break;
        case 'appConfigNoVisibility':
          global.AppConfig = scenario.value;
          break;
        case 'absentKeys':
          // Only a subset of columns included, all set to true; absent ones should default visible
          global.AppConfig = { columnVisibility: scenario.value };
          break;
        case 'nonBooleanValues':
          // Some columns have non-boolean values; they should default to visible
          global.AppConfig = { columnVisibility: scenario.value };
          break;
      }

      // Reset the container
      const caseList = mockElements['case-list'];
      caseList.children = [];
      caseList.hidden = true;
      caseList._innerHTML = '';
      mockElements['empty-state'].hidden = false;

      // Call the function under test
      renderCaseList(cases);

      // Find <th> elements in the rendered output
      const thElements = findAllByTag(caseList, 'TH');

      assert.strictEqual(
        thElements.length,
        6,
        'Expected 6 <th> elements (all columns visible) for scenario "' +
        scenario.type + '", but got ' + thElements.length
      );

      // Cleanup
      delete global.AppConfig;
    }),
    { numRuns: 100 }
  );
});

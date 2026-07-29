const fc = require('fast-check');
const { test } = require('node:test');
const assert = require('node:assert');

/**
 * Feature: case-list-table-render, Property 1: Bug Condition - Table Structure and Severity Badge Rendering
 * Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3
 *
 * For any non-empty array of cases passed to renderCaseList, the function SHALL
 * render a table element with class "case-list" containing a thead with th headers
 * and a tbody with one tr per case containing td cells. Severity badges SHALL have
 * class "severity-badge severity-badge--{level}" (BEM double-dash).
 *
 * IMPORTANT: This test encodes the EXPECTED (correct) behavior. It is expected to
 * FAIL on unfixed code, confirming the bug exists.
 */

// --- DOM mock setup ---
// A mock DOM that tracks element creation and tree structure so we can inspect
// the output of renderCaseList.

function createMockDOM() {
  function makeMockElement(tagName) {
    const el = {
      tagName: tagName.toUpperCase(),
      className: '',
      textContent: '',
      innerHTML: '',
      hidden: false,
      disabled: false,
      value: '',
      children: [],
      attributes: {},
      parentNode: null,
      type: '',
      setAttribute: function (name, value) {
        el.attributes[name] = value;
        if (name === 'role') el.role = value;
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
      querySelector: function (selector) {
        // Simple selector support for test purposes
        return null;
      },
    };
    // When innerHTML is set to '', clear children
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
  fc.stringOf(fc.constantFrom(...'abcdefghijklmnopqrstuvwxyz0123456789'.split('')), { minLength: 1, maxLength: 20 }),
  fc.stringOf(fc.constantFrom(...'abcdefghijklmnopqrstuvwxyz0123456789'.split('')), { minLength: 1, maxLength: 10 }),
  fc.constantFrom('.com', '.org', '.net', '.io')
).map(([local, domain, tld]) => `${local}@${domain}${tld}`);

// Severity: one of the allowed values
const severityArb = fc.constantFrom('low', 'medium', 'high', 'critical');

// Issue text
const issueArb = fc.string({ minLength: 1, maxLength: 200 });

// Response text
const responseArb = fc.string({ minLength: 0, maxLength: 200 });

// Full Case object arbitrary
const caseArb = fc.record({
  case_id: uuidArb,
  email: emailArb,
  issue: issueArb,
  severity: severityArb,
  response: responseArb,
});

// Non-empty array of cases
const casesArb = fc.array(caseArb, { minLength: 1, maxLength: 10 });

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

function findFirstByTag(root, tagName) {
  const all = findAllByTag(root, tagName);
  return all.length > 0 ? all[0] : null;
}

// --- Property-based test: Bug condition exploration ---

test('Property 1: Bug Condition - renderCaseList produces table structure with BEM severity badges', () => {
  /**
   * Validates: Requirements 2.1, 2.2, 2.3
   *
   * For any non-empty array of cases, renderCaseList SHALL produce:
   * - A table element with class "case-list" inside #case-list
   * - A thead with a tr containing 6 th elements
   * - A tbody with one tr per case
   * - Each tr contains td cells (not span elements)
   * - Severity badge class matches "severity-badge severity-badge--{level}"
   */
  fc.assert(
    fc.property(casesArb, (cases) => {
      // Reset the container
      const caseList = mockElements['case-list'];
      caseList.children = [];
      caseList.hidden = true;
      caseList._innerHTML = '';
      mockElements['empty-state'].hidden = false;

      // Call the function under test
      renderCaseList(cases);

      // --- Assertion 1: Container has a TABLE child with class "case-list" ---
      const table = findFirstByTag(caseList, 'TABLE');
      assert.ok(
        table !== null,
        'Expected #case-list to contain a <table> element, but no table found. ' +
        'Found children with tags: [' + caseList.children.map(c => c.tagName).join(', ') + ']'
      );
      assert.ok(
        table.className.indexOf('case-list') !== -1,
        'Expected table to have class "case-list", got: "' + table.className + '"'
      );

      // --- Assertion 2: Table has THEAD with TR containing 6 TH elements ---
      const thead = findFirstByTag(table, 'THEAD');
      assert.ok(thead !== null, 'Expected table to contain a <thead> element');

      const theadTr = findFirstByTag(thead, 'TR');
      assert.ok(theadTr !== null, 'Expected thead to contain a <tr> element');

      const thElements = findAllByTag(theadTr, 'TH');
      assert.strictEqual(
        thElements.length, 6,
        'Expected thead tr to have 6 <th> elements, got ' + thElements.length
      );

      const expectedHeaders = ['Case ID', 'Email', 'Issue', 'Severity', 'Response', 'Actions'];
      thElements.forEach(function (th, i) {
        assert.strictEqual(
          th.textContent, expectedHeaders[i],
          'Expected th[' + i + '] to be "' + expectedHeaders[i] + '", got "' + th.textContent + '"'
        );
      });

      // --- Assertion 3: Table has TBODY with one TR per case ---
      const tbody = findFirstByTag(table, 'TBODY');
      assert.ok(tbody !== null, 'Expected table to contain a <tbody> element');

      const bodyRows = findAllByTag(tbody, 'TR');
      assert.strictEqual(
        bodyRows.length, cases.length,
        'Expected tbody to have ' + cases.length + ' <tr> elements, got ' + bodyRows.length
      );

      // --- Assertion 4: Each TR contains TD cells (not SPAN) ---
      bodyRows.forEach(function (tr, rowIndex) {
        const tds = tr.children.filter(function (child) { return child.tagName === 'TD'; });
        assert.ok(
          tds.length > 0,
          'Expected row ' + rowIndex + ' to contain <td> cells, but found tags: [' +
          tr.children.map(c => c.tagName).join(', ') + ']'
        );
        const spans = tr.children.filter(function (child) { return child.tagName === 'SPAN'; });
        assert.strictEqual(
          spans.length, 0,
          'Expected row ' + rowIndex + ' to NOT contain <span> elements directly, but found ' + spans.length
        );
      });

      // --- Assertion 5: Severity badge class uses BEM double-dash ---
      bodyRows.forEach(function (tr, rowIndex) {
        const caseItem = cases[rowIndex];
        // Find the severity badge element in this row (it should be a span inside a td, or a td itself with the class)
        const allElements = [];
        function collectAll(node) {
          allElements.push(node);
          if (node.children) node.children.forEach(collectAll);
        }
        collectAll(tr);

        const severityEl = allElements.find(function (el) {
          return el.className && el.className.indexOf('severity-badge') !== -1;
        });

        assert.ok(
          severityEl !== undefined,
          'Expected row ' + rowIndex + ' to contain an element with class "severity-badge"'
        );

        const expectedClass = 'severity-badge severity-badge--' + caseItem.severity;
        assert.strictEqual(
          severityEl.className, expectedClass,
          'Expected severity badge class to be "' + expectedClass + '", got "' + severityEl.className + '"'
        );
      });
    }),
    { numRuns: 100 }
  );
});


// --- Property 2: Preservation - Non-Table Behaviors Unchanged ---

/**
 * Feature: case-list-table-render, Property 2: Preservation - Non-Table Behaviors Unchanged
 * Validates: Requirements 3.1, 3.2, 3.3
 *
 * For any empty/null/undefined input, renderCaseList SHALL trigger renderEmptyState
 * (empty-state shown, case-list hidden). For any non-empty case arrays, Edit and Delete
 * buttons SHALL have data-case-id matching caseItem.case_id. Issue and response text
 * SHALL be truncated via truncateText(text, 50) with max output length <= 53.
 */

// --- Helper: find all elements by tag recursively ---

function findAllButtons(root) {
  const results = [];
  function walk(node) {
    if (node.tagName === 'BUTTON') {
      results.push(node);
    }
    if (node.children) {
      node.children.forEach(walk);
    }
  }
  walk(root);
  return results;
}

// --- Preservation Property 2a: Empty/null/undefined inputs trigger empty state ---

test('Property 2a: Preservation - empty/null/undefined inputs show empty-state and hide case-list', () => {
  /**
   * Validates: Requirements 3.1
   *
   * For all empty/null/undefined inputs, renderEmptyState() is triggered:
   * empty-state.hidden === false and case-list.hidden === true.
   */
  const emptyInputs = [[], null, undefined];

  emptyInputs.forEach(function (input) {
    // Reset state
    mockElements['case-list'].children = [];
    mockElements['case-list'].hidden = false;
    mockElements['case-list']._innerHTML = '';
    mockElements['empty-state'].hidden = true;

    renderCaseList(input);

    assert.strictEqual(
      mockElements['empty-state'].hidden,
      false,
      'Expected empty-state.hidden to be false for input: ' + JSON.stringify(input)
    );
    assert.strictEqual(
      mockElements['case-list'].hidden,
      true,
      'Expected case-list.hidden to be true for input: ' + JSON.stringify(input)
    );
  });
});

// --- Preservation Property 2b: Edit/Delete buttons have correct data-case-id ---

test('Property 2b: Preservation - Edit and Delete buttons have correct data-case-id for all non-empty cases', () => {
  /**
   * Validates: Requirements 3.2
   *
   * For all non-empty case arrays, each case has Edit and Delete buttons
   * with data-case-id attribute matching caseItem.case_id.
   */
  fc.assert(
    fc.property(casesArb, (cases) => {
      // Reset the container
      const caseList = mockElements['case-list'];
      caseList.children = [];
      caseList.hidden = true;
      caseList._innerHTML = '';
      mockElements['empty-state'].hidden = false;

      // Call the function under test
      renderCaseList(cases);

      // Find all buttons in the rendered output
      const allButtons = findAllButtons(caseList);

      // For each case, there should be an Edit and a Delete button with matching data-case-id
      cases.forEach(function (caseItem) {
        const editBtn = allButtons.find(function (btn) {
          return btn.textContent === 'Edit' && btn.attributes['data-case-id'] === caseItem.case_id;
        });
        assert.ok(
          editBtn !== undefined,
          'Expected an Edit button with data-case-id="' + caseItem.case_id + '"'
        );

        const deleteBtn = allButtons.find(function (btn) {
          return btn.textContent === 'Delete' && btn.attributes['data-case-id'] === caseItem.case_id;
        });
        assert.ok(
          deleteBtn !== undefined,
          'Expected a Delete button with data-case-id="' + caseItem.case_id + '"'
        );
      });
    }),
    { numRuns: 100 }
  );
});

// --- Preservation Property 2c: Issue and response text truncation ---

test('Property 2c: Preservation - issue and response text are truncated to max 53 characters', () => {
  /**
   * Validates: Requirements 3.3
   *
   * For all non-empty case arrays, issue and response text in the rendered output
   * have length <= 53 (truncateText applied: 50 chars + "..." = 53 max).
   */

  // Helper: collect all textContent values from elements with a given className
  function findTextContentsByClass(root, className) {
    const results = [];
    function walk(node) {
      if (node.className && node.className.indexOf(className) !== -1) {
        results.push(node.textContent);
      }
      if (node.children) {
        node.children.forEach(walk);
      }
    }
    walk(root);
    return results;
  }

  fc.assert(
    fc.property(casesArb, (cases) => {
      // Reset the container
      const caseList = mockElements['case-list'];
      caseList.children = [];
      caseList.hidden = true;
      caseList._innerHTML = '';
      mockElements['empty-state'].hidden = false;

      // Call the function under test
      renderCaseList(cases);

      // Find issue text elements (class contains "case-issue")
      const issueTexts = findTextContentsByClass(caseList, 'case-issue');
      issueTexts.forEach(function (text, i) {
        assert.ok(
          text.length <= 53,
          'Expected issue text at index ' + i + ' to be <= 53 chars, got ' + text.length + ' chars: "' + text + '"'
        );
      });

      // Find response text elements (class contains "case-response")
      const responseTexts = findTextContentsByClass(caseList, 'case-response');
      responseTexts.forEach(function (text, i) {
        assert.ok(
          text.length <= 53,
          'Expected response text at index ' + i + ' to be <= 53 chars, got ' + text.length + ' chars: "' + text + '"'
        );
      });
    }),
    { numRuns: 100 }
  );
});

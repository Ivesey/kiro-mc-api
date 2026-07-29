const { test } = require('node:test');
const assert = require('node:assert');

/**
 * Unit tests for column visibility default and invalid configuration scenarios.
 * Validates: Requirements 4.1, 4.2, 5.1, 5.2
 */

// --- DOM mock setup (same pattern as ui.render.test.js) ---

function createMockDOM() {
  function makeMockElement(tagName) {
    var el = {
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
        var idx = el.children.indexOf(child);
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

  var elements = {};
  var ids = [
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
var mockElements = createMockDOM();

// Set up truncateText as global (ui.js uses it as a browser global)
var validation = require('../js/validation');
global.truncateText = validation.truncateText;

// Now require ui.js which will use the mocked globals
var ui = require('../js/ui');
var renderCaseList = ui.renderCaseList;
var isColumnVisible = ui.isColumnVisible;

// --- Sample case data ---
var sampleCase = { case_id: 'case-001', email: 'test@example.com', issue: 'Test issue', severity: 'low', response: 'Test response' };

// --- Helper: walk the DOM tree to find elements by tagName ---

function findAllByTag(root, tagName) {
  var results = [];
  var upperTag = tagName.toUpperCase();
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

// --- Helper: reset the mock DOM state and call renderCaseList ---

function resetAndRender(cases) {
  var caseList = mockElements['case-list'];
  caseList.children = [];
  caseList.hidden = true;
  caseList._innerHTML = '';
  mockElements['empty-state'].hidden = false;
  renderCaseList(cases);
  return caseList;
}

// --- Test 1: AppConfig undefined → 6 columns rendered ---

test('AppConfig undefined → 6 columns rendered', function () {
  // Ensure AppConfig is not defined
  delete global.AppConfig;

  var caseList = resetAndRender([sampleCase]);

  var thElements = findAllByTag(caseList, 'TH');
  assert.strictEqual(thElements.length, 6,
    'Expected 6 <th> elements when AppConfig is undefined, got ' + thElements.length);
});

// --- Test 2: columnVisibility missing → 6 columns rendered ---

test('columnVisibility missing → 6 columns rendered', function () {
  // Set AppConfig without columnVisibility property
  global.AppConfig = {};

  var caseList = resetAndRender([sampleCase]);

  var thElements = findAllByTag(caseList, 'TH');
  assert.strictEqual(thElements.length, 6,
    'Expected 6 <th> elements when columnVisibility is missing, got ' + thElements.length);

  // Cleanup
  delete global.AppConfig;
});

// --- Test 3: Column identifier absent from config → that column is visible ---

test('Column identifier absent from config → that column is visible', function () {
  // Only specify caseId and email; missing issue, severity, response, actions
  global.AppConfig = { columnVisibility: { caseId: true, email: true } };

  var caseList = resetAndRender([sampleCase]);

  var thElements = findAllByTag(caseList, 'TH');
  assert.strictEqual(thElements.length, 6,
    'Expected 6 <th> elements when some column identifiers are absent from config, got ' + thElements.length);

  // Cleanup
  delete global.AppConfig;
});

// --- Test 4: Non-boolean value for a column → that column is visible ---

test('Non-boolean value for a column → that column is visible', function () {
  // Set non-boolean values for columns
  global.AppConfig = {
    columnVisibility: {
      caseId: true,
      email: 'yes',
      issue: 42,
      severity: null,
      response: undefined,
      actions: {}
    }
  };

  var caseList = resetAndRender([sampleCase]);

  var thElements = findAllByTag(caseList, 'TH');
  assert.strictEqual(thElements.length, 6,
    'Expected 6 <th> elements when columns have non-boolean values, got ' + thElements.length);

  // Cleanup
  delete global.AppConfig;
});

// --- Test 5: Unknown keys in config → ignored, valid columns render normally ---

test('Unknown keys in config → ignored, valid columns render normally', function () {
  // Set all valid columns to true plus unknown keys
  global.AppConfig = {
    columnVisibility: {
      caseId: true,
      email: true,
      issue: true,
      severity: true,
      response: true,
      actions: true,
      foo: false,
      bar: true,
      unknownCol: false
    }
  };

  var caseList = resetAndRender([sampleCase]);

  var thElements = findAllByTag(caseList, 'TH');
  assert.strictEqual(thElements.length, 6,
    'Expected 6 <th> elements when unknown keys are present in config, got ' + thElements.length);

  // Cleanup
  delete global.AppConfig;
});

// --- Test 6: Hiding email and severity produces a 4-column table ---

test('Hiding email and severity produces a 4-column table', function () {
  global.AppConfig = { columnVisibility: { caseId: true, email: false, issue: true, severity: false, response: true, actions: true } };
  var caseList = resetAndRender([sampleCase]);
  var thElements = findAllByTag(caseList, 'TH');
  assert.strictEqual(thElements.length, 4);
  // Verify the correct 4 headers are present
  var headerTexts = thElements.map(function(th) { return th.textContent; });
  assert.deepStrictEqual(headerTexts, ['Case ID', 'Issue', 'Response', 'Actions']);
  delete global.AppConfig;
});

// --- Test 7: All columns hidden produces empty table structure ---

test('All columns hidden produces empty table structure (thead/tbody with no cells)', function () {
  global.AppConfig = { columnVisibility: { caseId: false, email: false, issue: false, severity: false, response: false, actions: false } };
  var caseList = resetAndRender([sampleCase]);
  var thElements = findAllByTag(caseList, 'TH');
  assert.strictEqual(thElements.length, 0);
  var tdElements = findAllByTag(caseList, 'TD');
  assert.strictEqual(tdElements.length, 0);
  // But table, thead, tbody should still exist
  var tables = findAllByTag(caseList, 'TABLE');
  assert.strictEqual(tables.length, 1);
  var theads = findAllByTag(caseList, 'THEAD');
  assert.strictEqual(theads.length, 1);
  var tbodys = findAllByTag(caseList, 'TBODY');
  assert.strictEqual(tbodys.length, 1);
  delete global.AppConfig;
});

// --- Test 8: Default config (all true) matches original 6-column behavior ---

test('Default config (all true) matches original 6-column behavior', function () {
  global.AppConfig = { columnVisibility: { caseId: true, email: true, issue: true, severity: true, response: true, actions: true } };
  var caseList = resetAndRender([sampleCase]);
  var thElements = findAllByTag(caseList, 'TH');
  assert.strictEqual(thElements.length, 6);
  var headerTexts = thElements.map(function(th) { return th.textContent; });
  assert.deepStrictEqual(headerTexts, ['Case ID', 'Email', 'Issue', 'Severity', 'Response', 'Actions']);
  delete global.AppConfig;
});

// --- Test 9: Script order in index.html ---

test('Script order in index.html has config.js before validation.js, api.js, ui.js, app.js', function () {
  var fs = require('fs');
  var path = require('path');
  var html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
  var scriptRegex = /<script src="js\/([^"]+)"><\/script>/g;
  var scripts = [];
  var match;
  while ((match = scriptRegex.exec(html)) !== null) {
    scripts.push(match[1]);
  }
  var expectedOrder = ['config.js', 'validation.js', 'api.js', 'ui.js', 'app.js'];
  assert.deepStrictEqual(scripts, expectedOrder);
});

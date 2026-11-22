// Regression tests for frontend/app.js (Issue #196)
const assert = require('node:assert');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

const row = (ticker = '', weight = '') => {
  const select = { value: ticker };
  const input = { value: weight };
  return {
    set innerHTML(html) {
      select.value = html.match(/value="([^"]+)" selected/)?.[1] ?? '';
    },
    querySelector: (s) => ({ select, input, '.weight-input': input, button: {} })[s],
  };
};

function createTestContext(fetchHandler) {
  const rows = [row('COST', '70'), row('JPM', '30')];
  const nodes = {
    'alert-banner': { querySelector: () => ({ onclick: null }), set innerHTML(_) {} },
    'preset-select': { value: 'Custom / Edited' },
    'api-base-url': { value: 'http://127.0.0.1:8000' },
    'assets-inputs': {
      set innerHTML(_) { rows.length = 0; },
      appendChild(r) { rows.push(r); },
      querySelectorAll: (s) => s === 'select' ? rows.map((r) => r.querySelector('select')) : rows,
    },
    'wf-inputs': { querySelectorAll: () => [] },
  };

  const ctx = vm.createContext({
    location: { pathname: '/app/', origin: 'http://127.0.0.1:8000' },
    document: {
      addEventListener() {}, querySelectorAll: () => [],
      getElementById: (id) => nodes[id] ??= {}, createElement: () => row(),
    },
    AbortController, setTimeout, clearTimeout,
    fetch: fetchHandler,
  });

  const appJsPath = path.join(__dirname, '..', 'frontend', 'app.js');
  vm.runInContext(fs.readFileSync(appJsPath, 'utf8'), ctx);
  ctx.bindEvents();
  return { ctx, nodes, rows };
}

async function testCheckConnectionPreservesCustomHoldings() {
  const { ctx, nodes } = createTestContext(async (url) => ({
    ok: true,
    json: async () => url.endsWith('/healthz') ? { status: 'healthy' } : {
      supported_tickers: ['NVDA', 'MSFT', 'GOOGL', 'ETH-USD', 'COST', 'JPM'], groups: {},
    },
  }));

  const before = ctx.readWeights('assets-inputs');
  assert.strictEqual(JSON.stringify(before), JSON.stringify({ COST: 70, JPM: 30 }));

  await nodes['btn-health'].onclick();

  const after = ctx.readWeights('assets-inputs');
  assert.strictEqual(JSON.stringify(after), JSON.stringify({ COST: 70, JPM: 30 }), 'Custom holdings should not be replaced by default preset');
  console.log('PASS: testCheckConnectionPreservesCustomHoldings');
}

async function testCheckConnectionFailureKeepsHoldings() {
  const { ctx, nodes } = createTestContext(async () => {
    throw new Error('Connection refused');
  });

  await nodes['btn-health'].onclick();
  const after = ctx.readWeights('assets-inputs');
  assert.strictEqual(JSON.stringify(after), JSON.stringify({ COST: 70, JPM: 30 }), 'Failed connection should preserve existing holdings');
  console.log('PASS: testCheckConnectionFailureKeepsHoldings');
}

async function runAll() {
  await testCheckConnectionPreservesCustomHoldings();
  await testCheckConnectionFailureKeepsHoldings();
  console.log('All frontend regression checks passed!');
}

runAll().catch((err) => {
  console.error(err);
  process.exit(1);
});

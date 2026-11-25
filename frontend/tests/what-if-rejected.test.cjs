const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { join } = require("node:path");
const { test } = require("node:test");
const { runInNewContext } = require("node:vm");

test("a rejected What-if comparison hides the previous result", async () => {
  const results = { hidden: false };
  const button = { disabled: false };
  let weights = { AAPL: 60, MSFT: 40 };
  let calls = 0;
  let fail = false;
  let alert;
  const context = {
    location: { pathname: "/app", origin: "http://localhost" },
    document: {
      addEventListener() {},
      getElementById(id) { return { "wf-results": results, "wf-run": button }[id]; },
    },
    fixture: {
      readWeights: () => weights,
      api: async () => {
        calls++;
        if (fail) throw new Error("Offline fixture");
        return { score: 42 };
      },
      showAlert: msg => { alert = msg; },
      renderWhatIf() {},
    },
  };
  runInNewContext(readFileSync(join(__dirname, "../app.js"), "utf8") + `
    analysis = { score: 40 };
    ({ readWeights, api, showAlert, renderWhatIf } = fixture);
  `, context);

  await context.runWhatIf();
  assert.equal(results.hidden, false);
  weights = { AAPL: 25, MSFT: 40 };
  await context.runWhatIf();
  assert.equal(results.hidden, true);
  assert.match(alert, /65.0%/);
  assert.equal(calls, 1);

  weights = { AAPL: 25, MSFT: 75 };
  await context.runWhatIf();
  assert.equal(results.hidden, false);
  fail = true;
  await context.runWhatIf();
  assert.equal(results.hidden, true);
  assert.match(alert, /Offline fixture/);
  assert.equal(button.disabled, false);
});

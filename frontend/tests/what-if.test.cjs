const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { join } = require("node:path");
const { test } = require("node:test");
const { runInNewContext } = require("node:vm");

test("What-if drawdowns are plotted on their own observation dates", () => {
  const nodes = new Map();
  let data;
  const context = {
    location: { pathname: "/app/", origin: "http://localhost" },
    document: {
      addEventListener() {},
      getElementById(id) {
        if (!nodes.has(id)) nodes.set(id, { getContext() { return id; } });
        return nodes.get(id);
      },
    },
    Chart: class {
      constructor(id, config) {
        assert.equal(id, "wfChart");
        data = JSON.parse(JSON.stringify(config.data));
      }
    },
  };
  runInNewContext(readFileSync(join(__dirname, "../app.js"), "utf8"), context);
  const base = {
    score: 40,
    level: "Medium",
    concentration: { top_asset: "AAPL", top_weight: 1, top3_weight: 1, effective_assets: 1 },
  };
  context.renderWhatIf(
    { ...base, dates: ["2026-11-20", "2026-11-23", "2026-11-24"], drawdown_series: [0, 0, 0] },
    { ...base, dates: ["2026-11-20", "2026-11-21", "2026-11-24"], drawdown_series: [0, -0.25, 0] }
  );
  assert.deepEqual(data.labels, ["2026-11-20", "2026-11-21", "2026-11-23", "2026-11-24"]);
  assert.deepEqual(data.datasets[0].data, [0, null, 0, 0]);
  assert.deepEqual(data.datasets[1].data, [0, -25, null, 0]);
});

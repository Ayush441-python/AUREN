import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { SAVED_PORTFOLIOS, resolveSavedPortfolio } from "../src/lib/savedPortfolios.ts";

const repoRoot = path.resolve(import.meta.dirname, "../..");

function loadUniverseTickers() {
  const py = fs.readFileSync(path.join(repoRoot, "engine/universe.py"), "utf8");
  const matches = [...py.matchAll(/^\s*"([A-Z0-9.\-]+)"\s*:/gm)].map((m) => m[1]);
  return new Set(matches);
}

test("all SavedPortfolios entries resolve to valid normalized supported tickers", () => {
  const supported = loadUniverseTickers();
  assert.equal(SAVED_PORTFOLIOS.length, 3);

  for (const id of ["p-balanced-01", "p-tech-tilt", "p-all-weather"]) {
    const entry = resolveSavedPortfolio(id);
    assert.ok(entry, `expected saved portfolio ${id} to resolve`);
    const keys = Object.keys(entry.weights);
    assert.equal(keys.length, entry.assets, `${id} asset count must match weight keys`);
    const sum = Object.values(entry.weights).reduce((a, b) => a + b, 0);
    assert.ok(Math.abs(sum - 1) < 1e-6, `${id} weights must sum to 1.0, got ${sum}`);
    for (const ticker of keys) {
      assert.ok(supported.has(ticker), `${id} ticker ${ticker} must exist in engine/universe.py`);
    }
  }
  assert.equal(resolveSavedPortfolio("non-existent-id"), undefined);
});

test("Workstation resolves portfolioId rather than ignoring it during initial risk fetch", () => {
  const ws = fs.readFileSync(
    path.join(repoRoot, "web/src/components/dashboard/Workstation.tsx"),
    "utf8"
  );
  assert.match(ws, /resolveSavedPortfolio\(portfolioId\)/);
  assert.match(ws, /\[portfolioId\]\);/);
  assert.match(ws, /<SavedPortfoliosView\s+onSelectPortfolio=/);
});

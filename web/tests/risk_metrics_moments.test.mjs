import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import {
  classifyKurtosisRegime,
  computeAdjustedExcessKurtosis,
  computeAdjustedSkewness,
  computeHorizonReturns,
  formatSignedMoment,
} from "../src/lib/returnMoments.ts";

test("positive upside jump produces positive G1 skewness (+sqrt(32)) and G2=32", () => {
  // 16 closes at 100 followed by 17 closes at 112.50 -> 1 +12.5% move, 31 zero moves
  const prices = [...Array(16).fill(100), ...Array(17).fill(112.5)];
  const r1d = computeHorizonReturns(prices, 1);
  assert.equal(r1d.length, 32);

  const skew1d = computeAdjustedSkewness(r1d);
  const kurt1d = computeAdjustedExcessKurtosis(r1d);
  assert.ok(skew1d !== null && Math.abs(skew1d - Math.sqrt(32)) < 1e-9);
  assert.ok(kurt1d !== null && Math.abs(kurt1d - 32) < 1e-9);
  assert.equal(formatSignedMoment(skew1d), "+5.66");
  assert.equal(formatSignedMoment(kurt1d), "+32.00");

  const r10d = computeHorizonReturns(prices, 10);
  const r1m = computeHorizonReturns(prices, 21);
  assert.equal(r10d.length, 23);
  assert.equal(r1m.length, 12);
  assert.ok((computeAdjustedSkewness(r10d) ?? 0) > 0);
});

test("downside jump produces negative G1 skewness (-sqrt(32)) and G2=32", () => {
  const prices = [...Array(16).fill(100), ...Array(17).fill(87.5)];
  const r1d = computeHorizonReturns(prices, 1);
  const skew1d = computeAdjustedSkewness(r1d);
  const kurt1d = computeAdjustedExcessKurtosis(r1d);
  assert.ok(skew1d !== null && Math.abs(skew1d + Math.sqrt(32)) < 1e-9);
  assert.ok(kurt1d !== null && Math.abs(kurt1d - 32) < 1e-9);
  assert.equal(formatSignedMoment(skew1d), "-5.66");
});

test("flat constant portfolio returns undefined moments and does not label Leptokurtic", () => {
  const prices = Array(33).fill(100);
  for (const h of [1, 10, 21]) {
    const r = computeHorizonReturns(prices, h);
    assert.equal(computeAdjustedSkewness(r), null);
    assert.equal(computeAdjustedExcessKurtosis(r), null);
    assert.equal(formatSignedMoment(computeAdjustedSkewness(r)), "N/A");
  }
  assert.equal(classifyKurtosisRegime(null), "Undefined (Zero Variance)");
});

test("RiskMetricsView uses computed moments rather than hardcoded literals", () => {
  const navViewsPath = path.resolve(
    import.meta.dirname,
    "../src/components/views/NavigationViews.tsx"
  );
  const source = fs.readFileSync(navViewsPath, "utf8");
  assert.match(source, /computeAdjustedSkewness/);
  assert.match(source, /computeAdjustedExcessKurtosis/);
  assert.match(source, /classifyKurtosisRegime/);
  assert.doesNotMatch(source, />-0\.34</);
  assert.doesNotMatch(source, />\+2\.18</);
});

import test from "node:test";
import assert from "node:assert/strict";

import { cellAppearance, highThreshold, lowThreshold } from "../src/components/dashboard/charts/heatmapCells.ts";

const LOW = "#6EE7B7";
const MODERATE = "#A39D90";
const ELEVATED = "#EACB83";
const HIGH = "#FCA5A5";

test("the legend's boundary: +0.20 is low, +0.21 is moderate (#408)", () => {
  assert.equal(cellAppearance(0.2, false).color, LOW);
  assert.equal(cellAppearance(0.21, false).color, MODERATE);
});

test("a genuinely uncorrelated pair is low, not moderate", () => {
  assert.equal(cellAppearance(0.1, false).color, LOW);
  assert.equal(cellAppearance(0, false).color, LOW);
});

test("negative correlations are still low", () => {
  assert.equal(cellAppearance(-0.21, false).color, LOW);
  assert.equal(cellAppearance(-0.99, false).color, LOW);
});

test("the other bands are unchanged", () => {
  assert.equal(cellAppearance(0.49, false).color, MODERATE);
  assert.equal(cellAppearance(0.5, false).color, ELEVATED);
  assert.equal(cellAppearance(0.7, false).color, ELEVATED);
  assert.equal(cellAppearance(0.71, false).color, HIGH);
  assert.equal(highThreshold, 0.7);
  assert.equal(lowThreshold, 0.2);
});

test("the diagonal keeps its own style whatever the value", () => {
  assert.equal(cellAppearance(1, true).color, "#77736C");
  assert.equal(cellAppearance(0, true).color, "#77736C");
});

test("colour intensity grows with magnitude but stays bounded", () => {
  const alpha = (v) => {
    const m = /rgba\(\d+,\d+,\d+,([0-9.]+)\)$/.exec(cellAppearance(v, false).backgroundColor);
    assert.ok(m, `unparsable colour for ${v}: ${cellAppearance(v, false).backgroundColor}`);
    return Number(m[1]);
  };
  assert.ok(alpha(0.9) > alpha(0.75));
  assert.ok(alpha(-0.6) > alpha(-0.3));
  assert.ok(Math.abs(alpha(-0.2) - alpha(0.2)) < 1e-9);
  assert.ok(alpha(1) <= 0.38 + 1e-9); // 0.12 + 0.26 at the high band
});

test("the issue's own fixture: 50/50 A and B with r = 0.10 renders two low cells", () => {
  const matrix = [[1, 0.1], [0.1, 1]];
  const cells = matrix.map((row, i) => row.map((value, j) => cellAppearance(value, i === j).color));
  assert.equal(cells[0][1], LOW);
  assert.equal(cells[1][0], LOW);
  assert.equal(cells[0][0], "#77736C");
});

import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";

const heatmapPath = path.resolve(
  import.meta.dirname,
  "../src/components/dashboard/charts/Heatmap.tsx"
);
const source = fs.readFileSync(heatmapPath, "utf8");

function loadInitialSelector() {
  const match = source.match(
    /export function getInitialHeatmapSelection\(matrix:\s*CorrelationMatrix\):\s*Selection \| null\s*(\{[\s\S]*?\n\})/
  );
  assert.ok(match, "getInitialHeatmapSelection must be exported from Heatmap.tsx");
  const fnSource = `
    const highThreshold = 0.7;
    function getInitialHeatmapSelection(matrix) ${match[1]}
    getInitialHeatmapSelection;
  `;
  const fn = vm.runInNewContext(fnSource);
  return (matrix) => structuredClone(fn(matrix));
}

test("singleton correlation matrix initializes selection from diagonal cell (1.00)", () => {
  const select = loadInitialSelector();
  const res = select({ columns: ["COST"], data: [[1]] });
  assert.deepEqual(res, {
    row: "COST",
    column: "COST",
    value: 1,
    high: false,
  });
});

test("two-asset low correlation matrix initializes off-diagonal pair", () => {
  const select = loadInitialSelector();
  const res = select({
    columns: ["NVDA", "GLD"],
    data: [
      [1, 0.28],
      [0.28, 1],
    ],
  });
  assert.deepEqual(res, {
    row: "NVDA",
    column: "GLD",
    value: 0.28,
    high: false,
  });
});

test("two-asset high correlation matrix flags off-diagonal pair as high", () => {
  const select = loadInitialSelector();
  const res = select({
    columns: ["NVDA", "AMD"],
    data: [
      [1, 0.85],
      [0.85, 1],
    ],
  });
  assert.deepEqual(res, {
    row: "NVDA",
    column: "AMD",
    value: 0.85,
    high: true,
  });
});

test("empty correlation matrix returns null initial selection", () => {
  const select = loadInitialSelector();
  assert.equal(select({ columns: [], data: [] }), null);
});

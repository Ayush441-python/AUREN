import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const navViewsPath = path.resolve(
  import.meta.dirname,
  "../src/components/views/NavigationViews.tsx"
);
const source = fs.readFileSync(navViewsPath, "utf8");

function getMarketOverviewSource() {
  const start = source.indexOf("export function MarketOverviewView");
  const end = source.indexOf("export function VolatilityAnalysisView", start);
  assert.ok(start !== -1 && end !== -1, "MarketOverviewView block must exist");
  return source.slice(start, end);
}

test("MarketOverviewView does not claim real-time market data for static figures", () => {
  const block = getMarketOverviewSource();
  assert.doesNotMatch(block, /real-time/i);
});

test("MarketOverviewView explicitly discloses illustrative sample data", () => {
  const block = getMarketOverviewSource();
  assert.match(block, /Illustrative Sample Data/i);
  assert.match(block, /Not Live Quotes/i);
  assert.match(block, /No live market-data feed is connected/i);
});

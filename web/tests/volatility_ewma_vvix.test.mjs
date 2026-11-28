import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import {
  computeEwmaAnnualizedVolatility,
  computeRealizedVolOfVol,
  computeSimpleReturns,
} from "../src/lib/volatilityMetrics.ts";

test("flat zero-variance price series yields 0 EWMA volatility and 0 vol-of-vol", () => {
  const prices = Array(35).fill(100);
  const rets = computeSimpleReturns(prices);
  assert.equal(rets.length, 34);
  assert.equal(computeEwmaAnnualizedVolatility(rets, 0.94), 0);
  assert.equal(computeRealizedVolOfVol(rets, 21), 0);
});

test("regime shift raises EWMA annualized volatility above calm baseline and yields positive vol-of-vol", () => {
  const calmPrices = [100];
  for (let i = 0; i < 24; i += 1) {
    calmPrices.push(calmPrices[calmPrices.length - 1] * (i % 2 === 0 ? 1.001 : 0.999));
  }
  const shockPrices = [...calmPrices];
  for (let i = 0; i < 12; i += 1) {
    shockPrices.push(shockPrices[shockPrices.length - 1] * (i % 2 === 0 ? 1.04 : 0.96));
  }

  const calmEwma = computeEwmaAnnualizedVolatility(computeSimpleReturns(calmPrices), 0.94);
  const shockRets = computeSimpleReturns(shockPrices);
  const shockEwma = computeEwmaAnnualizedVolatility(shockRets, 0.94);
  const volOfVol = computeRealizedVolOfVol(shockRets, 21);

  assert.ok(calmEwma !== null && shockEwma !== null && shockEwma > calmEwma * 4);
  assert.ok(volOfVol !== null && Number.isFinite(volOfVol) && volOfVol > 0);
});

test("short series returns null realized vol-of-vol rather than synthetic constants", () => {
  const rets = Array(15).fill(0.01);
  assert.equal(computeRealizedVolOfVol(rets, 21), null);
});

test("VolatilityAnalysisView computes EWMA and realized vol-of-vol without hardcoded 88.4", () => {
  const navViewsPath = path.resolve(
    import.meta.dirname,
    "../src/components/views/NavigationViews.tsx"
  );
  const source = fs.readFileSync(navViewsPath, "utf8");
  assert.match(source, /computeEwmaAnnualizedVolatility/);
  assert.match(source, /computeRealizedVolOfVol/);
  assert.doesNotMatch(source, />88\.4</);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { computeDerivedQuantMetrics } from '../src/lib/quantMetrics.ts';

// Load actual bundled historical prices from AUREN's data/prices.csv
function loadBundledPrices(tickers) {
  const csv = fs.readFileSync(new URL('../../data/prices.csv', import.meta.url), 'utf8').trim().split(/\r?\n/);
  const headers = csv[0].split(',');
  const colIdx = Object.fromEntries(tickers.map((t) => [t, headers.indexOf(t)]));
  const rows = [];
  for (let r = 1; r < csv.length; r++) {
    const cols = csv[r].split(',');
    const vals = tickers.map((t) => Number(cols[colIdx[t]]));
    if (vals.every((v) => Number.isFinite(v) && v > 0)) {
      rows.push(vals);
    }
  }
  const priceSeries = {};
  tickers.forEach((t, ti) => {
    const p0 = rows[0][ti];
    priceSeries[t] = rows.map((row) => Number(((row[ti] / p0) * 100).toFixed(2)));
  });
  return { rows, priceSeries };
}

test('AUREN Maths Bounty Reproduction #1: Single-asset 100% NVDA violates portfolio variance identity under charCodeAt formula', () => {
  const { priceSeries } = loadBundledPrices(['NVDA']);
  priceSeries['Portfolio'] = priceSeries['NVDA'];

  // Compute true annualized volatility of NVDA from bundled prices.csv
  const rets = [];
  for (let i = 1; i < priceSeries['NVDA'].length; i++) {
    rets.push(priceSeries['NVDA'][i] / priceSeries['NVDA'][i - 1] - 1);
  }
  const mean = rets.reduce((a, b) => a + b, 0) / rets.length;
  const std = Math.sqrt(rets.reduce((a, r) => a + (r - mean) ** 2, 0) / (rets.length - 1));
  const portVol = std * Math.sqrt(252);

  // Legacy buggy formula in NavigationViews.tsx:311:
  // const assetVol = data.volatility * (0.8 + (ticker.charCodeAt(0) % 5) * 0.1);
  // 'N'.charCodeAt(0) === 78 -> 78 % 5 === 3 -> 1.10 * portVol (+10% impossible inflation on a 100% single-asset portfolio!)
  const buggyNvdaVol = portVol * (0.8 + ('NVDA'.charCodeAt(0) % 5) * 0.1);
  assert.ok(Math.abs(buggyNvdaVol / portVol - 1.1) < 1e-9);

  // Fixed calculation matches w=[1] variance identity sigma_p === sigma_NVDA
  const fixed = computeDerivedQuantMetrics({
    priceSeries,
    normalizedWeights: { NVDA: 1.0 },
    portfolioVolatility: portVol,
    maxDrawdown: -0.35
  });
  assert.equal(fixed.assetVolatilities.length, 1);
  assert.ok(Math.abs(fixed.assetVolatilities[0].volatility - portVol) < 1e-9);
});

test('AUREN Maths Bounty Reproduction #2: 50% BTC-USD / 50% GLD receives identical fake volatilities under charCodeAt modulo 5', () => {
  const { rows, priceSeries } = loadBundledPrices(['BTC-USD', 'GLD']);
  const weights = { 'BTC-USD': 0.5, GLD: 0.5 };

  // Build Portfolio cumulative series (constant-mix daily returns as in engine/metrics.py)
  let cum = 100;
  const port = [100];
  const portRets = [];
  for (let i = 1; i < rows.length; i++) {
    const rBtc = rows[i][0] / rows[i - 1][0] - 1;
    const rGld = rows[i][1] / rows[i - 1][1] - 1;
    const rp = 0.5 * rBtc + 0.5 * rGld;
    portRets.push(rp);
    cum *= 1 + rp;
    port.push(Number(cum.toFixed(2)));
  }
  priceSeries['Portfolio'] = port;
  const mean = portRets.reduce((a, b) => a + b, 0) / portRets.length;
  const portVol = Math.sqrt(portRets.reduce((a, r) => a + (r - mean) ** 2, 0) / (portRets.length - 1)) * Math.sqrt(252);

  // Legacy bug: 'B'.charCodeAt(0) = 66 (66 % 5 = 1), 'G'.charCodeAt(0) = 71 (71 % 5 = 1)
  // Both BTC-USD and GLD were assigned 0.9 * portVol!
  const buggyBtc = portVol * (0.8 + ('BTC-USD'.charCodeAt(0) % 5) * 0.1);
  const buggyGld = portVol * (0.8 + ('GLD'.charCodeAt(0) % 5) * 0.1);
  assert.equal(buggyBtc, buggyGld);

  // Fixed calculation recovers true BTC-USD vol >> GLD vol and sorts BTC-USD first
  const fixed = computeDerivedQuantMetrics({
    priceSeries,
    normalizedWeights: weights,
    portfolioVolatility: portVol,
    maxDrawdown: -0.25
  });
  assert.equal(fixed.assetVolatilities[0].ticker, 'BTC-USD');
  assert.equal(fixed.assetVolatilities[1].ticker, 'GLD');
  assert.ok(
    fixed.assetVolatilities[0].volatility > fixed.assetVolatilities[1].volatility * 1.6,
    `Expected BTC-USD vol (${fixed.assetVolatilities[0].volatility}) > 1.6x GLD vol (${fixed.assetVolatilities[1].volatility})`
  );
  console.log('Verified BTC-USD vs GLD realized vol:', fixed.assetVolatilities);
});

test('AUREN Maths Bounty Reproduction #3: Losing portfolio (-45% return) gets positive Calmar/Sortino and Sortino===2*Calmar under legacy formula', () => {
  // Construct 252-day losing portfolio series ending at 55.0 (-45% CAGR, -45% max drawdown, ~42% annualized vol)
  const port = [100];
  let cur = 100;
  for (let d = 1; d <= 252; d++) {
    const step = d % 2 === 0 ? 0.022 : -0.0265;
    cur *= 1 + step;
    port.push(cur);
  }
  const rets = [];
  for (let i = 1; i < port.length; i++) rets.push(port[i] / port[i - 1] - 1);
  const mean = rets.reduce((a, b) => a + b, 0) / rets.length;
  const vol = Math.sqrt(rets.reduce((a, r) => a + (r - mean) ** 2, 0) / (rets.length - 1)) * Math.sqrt(252);
  let peak = 100;
  let mdd = 0;
  for (const v of port) {
    if (v > peak) peak = v;
    const dd = v / peak - 1;
    if (dd < mdd) mdd = dd;
  }

  // Legacy buggy formulas in NavigationViews.tsx:41-45:
  const buggyAnnRet = vol * 0.65; // Positive!
  const buggyCalmar = buggyAnnRet / Math.abs(mdd); // Positive on a heavy loser!
  const buggySortino = buggyAnnRet / (Math.abs(mdd) * 0.5); // Identically 2 * buggyCalmar!
  assert.ok(buggyCalmar > 0.5, 'Legacy Calmar is falsely positive on losing portfolio');
  assert.ok(Math.abs(buggySortino - 2 * buggyCalmar) < 1e-12, 'Legacy Sortino is trivially 2 * Calmar');

  // Fixed formulas produce negative CAGR, negative Calmar, and true LPM_2 Sortino != 2 * Calmar
  const fixed = computeDerivedQuantMetrics({
    priceSeries: { Portfolio: port, INTC: port },
    normalizedWeights: { INTC: 1.0 },
    portfolioVolatility: vol,
    maxDrawdown: mdd
  });
  assert.ok(fixed.annualizedReturn < -0.4, `Expected negative CAGR, got ${fixed.annualizedReturn}`);
  assert.ok(fixed.calmarRatio < -0.8, `Expected negative Calmar, got ${fixed.calmarRatio}`);
  assert.ok(fixed.sortinoRatio < -1.0, `Expected negative Sortino, got ${fixed.sortinoRatio}`);
  assert.notEqual(Math.sign(fixed.calmarRatio), Math.sign(buggyCalmar));
  console.log('Losing portfolio legacy vs fixed:', {
    buggyCalmar: buggyCalmar.toFixed(2),
    buggySortino: buggySortino.toFixed(2),
    fixedCagr: fixed.annualizedReturn.toFixed(4),
    fixedCalmar: fixed.calmarRatio.toFixed(2),
    fixedSortino: fixed.sortinoRatio.toFixed(2)
  });
});

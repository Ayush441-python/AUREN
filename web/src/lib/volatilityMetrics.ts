/**
 * Volatility second-order metrics computed from the price series the API already
 * returns, so the volatility view stops showing literals.
 *
 * Every function is pure and total: a flat series gives 0, a series too short to
 * say anything gives null, and nothing throws on the messy input a chart can
 * receive (empty arrays, zeros, NaN).
 */

/** Simple (not log) returns: (p[i] − p[i−1]) / p[i−1]. Zeros and NaN are skipped. */
export function computeSimpleReturns(prices: number[]): number[] {
  const out: number[] = [];
  for (let i = 1; i < prices.length; i++) {
    const previous = prices[i - 1];
    const current = prices[i];
    if (!Number.isFinite(previous) || !Number.isFinite(current) || previous === 0) continue;
    out.push(current / previous - 1);
  }
  return out;
}

/**
 * RiskMetrics EWMA annualised volatility.
 *
 * σ²_t = λ·σ²_{t−1} + (1 − λ)·r²_t, seeded with the first squared return.
 * Returns 0 for a flat series and null when there are fewer than two returns.
 */
export function computeEwmaAnnualizedVolatility(
  returns: number[],
  lambda = 0.94,
  periodsPerYear = 252,
): number | null {
  if (returns.length < 2) return null;

  let variance = returns[0] * returns[0];
  for (let i = 1; i < returns.length; i++) {
    variance = lambda * variance + (1 - lambda) * returns[i] * returns[i];
  }

  if (!Number.isFinite(variance) || variance <= 0) return 0;
  return Math.sqrt(variance * periodsPerYear);
}

/**
 * Realised volatility-of-volatility: the sample standard deviation of the
 * rolling `window`-session annualised volatility.
 *
 * Returns 0 when every window is flat, null when there are not enough returns to
 * form at least two windows (fewer than window + 1 returns).
 */
export function computeRealizedVolOfVol(
  returns: number[],
  window = 21,
  periodsPerYear = 252,
): number | null {
  if (window < 2 || returns.length < window + 1) return null;

  const rollingVols: number[] = [];
  for (let end = window; end <= returns.length; end++) {
    const slice = returns.slice(end - window, end);
    const mean = slice.reduce((sum, r) => sum + r, 0) / slice.length;
    const variance = slice.reduce((sum, r) => sum + (r - mean) ** 2, 0) / (slice.length - 1);
    rollingVols.push(Math.sqrt(Math.max(variance, 0) * periodsPerYear));
  }

  if (rollingVols.length < 2) return null;

  const mean = rollingVols.reduce((sum, v) => sum + v, 0) / rollingVols.length;
  const variance = rollingVols.reduce((sum, v) => sum + (v - mean) ** 2, 0) / (rollingVols.length - 1);
  if (!Number.isFinite(variance) || variance <= 0) return 0;
  return Math.sqrt(variance);
}

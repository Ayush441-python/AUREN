/**
 * Simple 1-period return series derived from positive closing prices.
 */
export function computeSimpleReturns(prices: readonly number[]): number[] {
  if (!Array.isArray(prices) || prices.length < 2) {
    return [];
  }
  const out: number[] = [];
  for (let i = 1; i < prices.length; i += 1) {
    const prev = prices[i - 1];
    const curr = prices[i];
    if (Number.isFinite(prev) && Number.isFinite(curr) && prev > 0) {
      out.push(curr / prev - 1);
    }
  }
  return out;
}

/**
 * RiskMetrics EWMA annualized volatility using variance recursion:
 * sigma_t^2 = lambda * sigma_{t-1}^2 + (1 - lambda) * r_t^2.
 * Returns 0 on flat constant series and null when fewer than 2 returns exist.
 */
export function computeEwmaAnnualizedVolatility(
  returns: readonly number[],
  lambda = 0.94,
  periodsPerYear = 252
): number | null {
  const clean = returns.filter((r) => Number.isFinite(r));
  if (clean.length < 2 || lambda <= 0 || lambda >= 1) {
    return null;
  }

  let variance = clean[0] * clean[0];
  for (let i = 1; i < clean.length; i += 1) {
    const r = clean[i];
    variance = lambda * variance + (1 - lambda) * r * r;
  }
  if (!Number.isFinite(variance) || variance < 1e-20) {
    return 0;
  }
  return Math.sqrt(variance * periodsPerYear);
}

/**
 * Realized Volatility-of-Volatility: sample standard deviation across rolling
 * `window`-session annualized volatility estimates.
 * Returns 0 on constant flat series and null when fewer than `window + 1` returns exist.
 */
export function computeRealizedVolOfVol(
  returns: readonly number[],
  window = 21,
  periodsPerYear = 252
): number | null {
  const clean = returns.filter((r) => Number.isFinite(r));
  if (clean.length < window + 1 || window < 2) {
    return null;
  }

  const rollingVols: number[] = [];
  for (let start = 0; start + window <= clean.length; start += 1) {
    const slice = clean.slice(start, start + window);
    let mean = 0;
    for (const r of slice) mean += r;
    mean /= window;

    let ss = 0;
    for (const r of slice) {
      const d = r - mean;
      ss += d * d;
    }
    const std = Math.sqrt(ss / (window - 1));
    rollingVols.push(std * Math.sqrt(periodsPerYear));
  }

  if (rollingVols.length < 2) {
    return null;
  }
  let vMean = 0;
  for (const v of rollingVols) vMean += v;
  vMean /= rollingVols.length;

  let vSs = 0;
  for (const v of rollingVols) {
    const d = v - vMean;
    vSs += d * d;
  }
  const volOfVol = Math.sqrt(vSs / (rollingVols.length - 1));
  return !Number.isFinite(volOfVol) || volOfVol < 1e-12 ? 0 : volOfVol;
}

/**
 * Higher moments of a return series (skewness and excess kurtosis), with the
 * sample-size corrections the worked example in #361 uses.
 *
 * Every function is total: a flat series — where the standard deviation is zero
 * and no standardised moment is defined — returns null instead of a number, and
 * a series too short to say anything also returns null. Nothing is shown when it
 * cannot be computed, which is the opposite of printing a constant.
 */

/** Simple returns: `(p[i] − p[i−1]) / p[i−1]`, skipping zeros and non-finite values. */
export function simpleReturns(prices: number[]): number[] {
  const out: number[] = [];
  for (let i = 1; i < prices.length; i++) {
    const previous = prices[i - 1];
    const current = prices[i];
    if (!Number.isFinite(previous) || !Number.isFinite(current) || previous === 0) continue;
    out.push(current / previous - 1);
  }
  return out;
}

/** Compound `sessions` consecutive simple returns into overlapping horizon returns. */
export function horizonReturns(returns: number[], sessions: number): number[] {
  if (sessions < 1 || returns.length < sessions) return [];
  const out: number[] = [];
  for (let end = sessions; end <= returns.length; end++) {
    let growth = 1;
    for (let i = end - sessions; i < end; i++) growth *= 1 + returns[i];
    out.push(growth - 1);
  }
  return out;
}

function centralMoments(returns: number[]): { n: number; mean: number; m2: number; m3: number; m4: number } | null {
  const n = returns.length;
  if (n < 2) return null;
  const mean = returns.reduce((sum, r) => sum + r, 0) / n;
  let m2 = 0;
  let m3 = 0;
  let m4 = 0;
  for (const r of returns) {
    const d = r - mean;
    m2 += d * d;
    m3 += d * d * d;
    m4 += d * d * d * d;
  }
  return { n, mean, m2: m2 / n, m3: m3 / n, m4: m4 / n };
}

/**
 * Adjusted Fisher–Pearson sample skewness:
 * `g1 = m3 / m2^(3/2)`, then `G1 = g1 · √(n(n−1)) / (n−2)`.
 *
 * One nonzero return among n gives `sign(move)·√n`; a flat series gives null.
 */
export function computeAdjustedSkewness(returns: number[]): number | null {
  const m = centralMoments(returns);
  if (!m || m.n < 3 || m.m2 === 0) return null;
  const g1 = m.m3 / Math.pow(m.m2, 1.5);
  const corrected = (g1 * Math.sqrt(m.n * (m.n - 1))) / (m.n - 2);
  return Number.isFinite(corrected) ? corrected : null;
}

/**
 * Bias-corrected Fisher excess kurtosis:
 * `g2 = m4 / m2² − 3`, then `G2 = ((n−1)/((n−2)(n−3))) · ((n+1)·g2 + 6)`.
 *
 * One nonzero return among n gives `n`; a flat series gives null.
 */
export function computeExcessKurtosis(returns: number[]): number | null {
  const m = centralMoments(returns);
  if (!m || m.n < 4 || m.m2 === 0) return null;
  const g2 = m.m4 / (m.m2 * m.m2) - 3;
  const corrected = ((m.n - 1) / ((m.n - 2) * (m.n - 3))) * ((m.n + 1) * g2 + 6);
  return Number.isFinite(corrected) ? corrected : null;
}

/** Signed fixed-point rendering for a moment that may not be defined. */
export function formatMoment(value: number | null, digits = 2): string {
  if (value === null || !Number.isFinite(value)) return "—";
  const text = value.toFixed(digits);
  return value > 0 ? `+${text}` : text;
}

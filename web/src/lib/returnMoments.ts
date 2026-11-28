/**
 * Computes overlapping simple returns over a fixed session horizon from a price series.
 */
export function computeHorizonReturns(
  prices: readonly number[],
  horizon: number
): number[] {
  if (!Array.isArray(prices) || horizon < 1 || prices.length <= horizon) {
    return [];
  }
  const returns: number[] = [];
  for (let i = 0; i + horizon < prices.length; i += 1) {
    const start = prices[i];
    const end = prices[i + horizon];
    if (Number.isFinite(start) && Number.isFinite(end) && start > 0) {
      returns.push(end / start - 1);
    }
  }
  return returns;
}

function summarizeMoments(returns: readonly number[]): {
  n: number;
  mean: number;
  sd: number;
} | null {
  const clean = returns.filter((x) => Number.isFinite(x));
  const n = clean.length;
  if (n < 3) return null;

  let sum = 0;
  for (const x of clean) sum += x;
  const mean = sum / n;

  let sumSq = 0;
  for (const x of clean) {
    const d = x - mean;
    sumSq += d * d;
  }
  const variance = sumSq / (n - 1);
  const sd = Math.sqrt(variance);
  if (!Number.isFinite(sd) || sd <= 1e-12) {
    return null;
  }
  return { n, mean, sd };
}

/**
 * Adjusted Fisher-Pearson sample skewness coefficient (G1).
 * Returns null when fewer than 3 observations exist or standard deviation is zero.
 */
export function computeAdjustedSkewness(returns: readonly number[]): number | null {
  const clean = returns.filter((x) => Number.isFinite(x));
  const stats = summarizeMoments(clean);
  if (!stats || stats.n < 3) return null;

  const { n, mean, sd } = stats;
  let sumCube = 0;
  for (const x of clean) {
    const z = (x - mean) / sd;
    sumCube += z * z * z;
  }
  return (n / ((n - 1) * (n - 2))) * sumCube;
}

/**
 * Bias-corrected Fisher sample excess kurtosis (G2).
 * Returns null when fewer than 4 observations exist or standard deviation is zero.
 */
export function computeAdjustedExcessKurtosis(
  returns: readonly number[]
): number | null {
  const clean = returns.filter((x) => Number.isFinite(x));
  const stats = summarizeMoments(clean);
  if (!stats || stats.n < 4) return null;

  const { n, mean, sd } = stats;
  let sumFourth = 0;
  for (const x of clean) {
    const z = (x - mean) / sd;
    const z2 = z * z;
    sumFourth += z2 * z2;
  }
  const term1 = ((n * (n + 1)) / ((n - 1) * (n - 2) * (n - 3))) * sumFourth;
  const term2 = (3 * (n - 1) * (n - 1)) / ((n - 2) * (n - 3));
  return term1 - term2;
}

/**
 * Classifies distribution tail regime from sample excess kurtosis.
 */
export function classifyKurtosisRegime(excessKurtosis: number | null): string {
  if (excessKurtosis === null || !Number.isFinite(excessKurtosis)) {
    return "Undefined (Zero Variance)";
  }
  if (excessKurtosis > 0.25) {
    return "Leptokurtic (Fat Tails)";
  }
  if (excessKurtosis < -0.25) {
    return "Platykurtic (Thin Tails)";
  }
  return "Mesokurtic (Near-Normal)";
}

/**
 * Formats a signed standardized moment value for display, returning "N/A" when undefined.
 */
export function formatSignedMoment(value: number | null): string {
  if (value === null || !Number.isFinite(value)) {
    return "N/A";
  }
  if (Math.abs(value) < 0.005) {
    return "0.00";
  }
  return value > 0 ? `+${value.toFixed(2)}` : value.toFixed(2);
}

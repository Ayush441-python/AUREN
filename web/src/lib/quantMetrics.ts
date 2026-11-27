// Mathematically sound risk & return ratios computed directly from historical daily price series

export interface DerivedQuantMetrics {
  annualizedReturn: number;
  sharpeRatio: number;
  sortinoRatio: number;
  calmarRatio: number;
  skewness: number;
  excessKurtosis: number;
  assetVolatilities: { ticker: string; weight: number; volatility: number }[];
}

export const RISK_FREE_ANNUAL = 0.0425; // 4.25% US 10Y Treasury benchmark displayed in UI
export const TRADING_DAYS = 252;

export function dailyReturnsFromSeries(series: number[] | undefined): number[] {
  if (!series || series.length < 2) return [];
  const out: number[] = [];
  for (let i = 1; i < series.length; i++) {
    const prev = series[i - 1]!;
    const cur = series[i]!;
    if (Number.isFinite(prev) && Number.isFinite(cur) && prev > 0) {
      out.push(cur / prev - 1);
    }
  }
  return out;
}

export function annualizedVolatilityFromSeries(series: number[] | undefined): number | null {
  const rets = dailyReturnsFromSeries(series);
  if (rets.length < 2) return null;
  const n = rets.length;
  let mean = 0;
  for (let i = 0; i < n; i++) mean += rets[i]!;
  mean /= n;
  let sumSq = 0;
  for (let i = 0; i < n; i++) {
    const d = rets[i]! - mean;
    sumSq += d * d;
  }
  const sampleStd = Math.sqrt(sumSq / (n - 1));
  return sampleStd * Math.sqrt(TRADING_DAYS);
}

export function computeDerivedQuantMetrics(params: {
  priceSeries: Record<string, number[]>;
  normalizedWeights: Record<string, number>;
  portfolioVolatility: number;
  maxDrawdown: number;
  riskFreeAnnual?: number;
}): DerivedQuantMetrics {
  const {
    priceSeries,
    normalizedWeights,
    portfolioVolatility,
    maxDrawdown,
    riskFreeAnnual = RISK_FREE_ANNUAL
  } = params;

  const portSeries = priceSeries['Portfolio'];
  const rets = dailyReturnsFromSeries(portSeries);
  const n = rets.length;
  const rfDaily = Math.pow(1 + riskFreeAnnual, 1 / TRADING_DAYS) - 1;

  // 1. Compound Annual Growth Rate (CAGR) from cumulative portfolio index V_0 .. V_T
  let annualizedReturn = 0;
  if (portSeries && portSeries.length >= 2 && portSeries[0]! > 0 && portSeries[portSeries.length - 1]! > 0) {
    const totalGrowth = portSeries[portSeries.length - 1]! / portSeries[0]!;
    annualizedReturn = Math.pow(totalGrowth, TRADING_DAYS / n) - 1;
  }

  // 2. Annualized Sharpe Ratio = (Arithmetic Annualized Excess Return) / Annualized Volatility
  let meanDaily = 0;
  if (n > 0) {
    for (let i = 0; i < n; i++) meanDaily += rets[i]!;
    meanDaily /= n;
  }
  const excessAnnual = n > 0 ? (meanDaily - rfDaily) * TRADING_DAYS : -riskFreeAnnual;
  const sharpeRatio = portfolioVolatility > 1e-9 ? excessAnnual / portfolioVolatility : 0;

  // 3. Annualized Sortino Ratio using true lower partial moment LPM_2 below daily MAR = rfDaily
  let downsideSqSum = 0;
  for (let i = 0; i < n; i++) {
    const diff = rets[i]! - rfDaily;
    if (diff < 0) downsideSqSum += diff * diff;
  }
  const downsideDevAnnual = n > 0 ? Math.sqrt(downsideSqSum / n) * Math.sqrt(TRADING_DAYS) : 0;
  const sortinoRatio = downsideDevAnnual > 1e-9 ? excessAnnual / downsideDevAnnual : 0;

  // 4. Calmar Ratio = CAGR / |Max Drawdown|
  const absMdd = Math.abs(maxDrawdown);
  const calmarRatio = absMdd > 1e-9 ? annualizedReturn / absMdd : 0;

  // 5. Adjusted Fisher-Pearson sample skewness (G1) & sample excess kurtosis (G2)
  let skewness = 0;
  let excessKurtosis = 0;
  if (n >= 4) {
    let m2 = 0;
    let m3 = 0;
    let m4 = 0;
    for (let i = 0; i < n; i++) {
      const d = rets[i]! - meanDaily;
      const d2 = d * d;
      m2 += d2;
      m3 += d2 * d;
      m4 += d2 * d2;
    }
    const s2 = m2 / (n - 1);
    const s = Math.sqrt(s2);
    if (s > 1e-12) {
      skewness = (n / ((n - 1) * (n - 2))) * (m3 / (s2 * s));
      excessKurtosis =
        ((n * (n + 1)) / ((n - 1) * (n - 2) * (n - 3))) * (m4 / (s2 * s2)) -
        (3 * (n - 1) * (n - 1)) / ((n - 2) * (n - 3));
    }
  }

  // 6. Per-asset realized annualized volatility from each holding's actual price_series[ticker], sorted descending
  const assetVolatilities = Object.entries(normalizedWeights)
    .map(([ticker, weight]) => {
      const realized = annualizedVolatilityFromSeries(priceSeries[ticker]);
      return {
        ticker,
        weight,
        volatility: realized ?? portfolioVolatility
      };
    })
    .sort((a, b) => b.volatility - a.volatility || b.weight - a.weight || a.ticker.localeCompare(b.ticker));

  return {
    annualizedReturn,
    sharpeRatio,
    sortinoRatio,
    calmarRatio,
    skewness,
    excessKurtosis,
    assetVolatilities
  };
}

export type RiskLevel = "Low" | "Medium" | "High";

export interface ConcentrationMetrics {
  top_asset: string;
  top_weight: number;
  top3_weight: number;
  hhi: number;
  effective_assets: number;
}

export interface CorrelationMatrix {
  columns: string[];
  data: number[][];
}

export interface RiskAnalysis {
  score: number;
  level: RiskLevel;
  normalized_weights: Record<string, number>;
  reasons: string[];
  hits: [number, string][];
  dates: string[];
  price_series: Record<string, number[]>;
  drawdown_series: number[];
  correlation_matrix: CorrelationMatrix;
  concentration: ConcentrationMetrics;
  volatility: number;
  max_drawdown: number;
  sector_exposure: Record<string, number>;
  group_exposure?: Record<string, number>;
  groups?: Record<string, string>;
  correlated_pairs: [string, string, number][];
  stress: Record<string, number>;
  worst_historical_periods: {
    worst_day: number;
    worst_month: number;
  };
  disclaimer: string;
}

export interface LiquidityAsset {
  ticker: string;
  weight: number;
  holding_value: number;
  adv: number | null;
  days_to_exit: number | null;
}

export interface LiquidityAnalysis {
  portfolio_value: number;
  adv_participation: number;
  max_days_to_exit: number;
  assets: LiquidityAsset[];
}

export interface WalletHolding {
  token: string;
  ticker: string;
  address: string;
  tokens: number;
  shares: number;
  price: number;
  value: number;
  supported: boolean;
  nav_updated: string | null;
}

export interface WalletResponse {
  address: string;
  holdings_count: number;
  tokens_checked: number;
  holdings: WalletHolding[];
  portfolio: Record<string, number>;
  total_value: number;
  skipped_count: number;
  has_holdings?: boolean;
  message?: string;
}

export interface AIReportResponse {
  report: string;
  model: string;
  unverified_numbers: number[];
  disclaimer: string;
}

export interface UniverseData {
  sectors: Record<string, string>;
  groups: Record<string, string>;
  supported_tickers: string[];
}

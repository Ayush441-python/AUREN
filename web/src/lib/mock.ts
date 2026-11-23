import { RiskAnalysis } from "./types";

export const BASE_PORTFOLIO_ANALYSIS: RiskAnalysis = {
  score: 64,
  level: "Medium",
  normalized_weights: {
    AAPL: 0.35,
    NVDA: 0.25,
    "ETH-USD": 0.20,
    "BTC-USD": 0.15,
    USDC: 0.05,
  },
  reasons: [
    "Top holding AAPL represents 35.0% of portfolio, exceeding the 25% single-asset safety benchmark.",
    "Combined Technology exposure (AAPL + NVDA) is 60.0%, creating sector concentration vulnerability.",
    "Crypto asset correlation (ETH-USD and BTC-USD: +0.84) limits diversification benefit during digital asset drawdowns.",
    "Portfolio historical Max Drawdown reached -38.4% during 2022 market contraction.",
  ],
  hits: [
    [15, "Single-asset concentration: AAPL exceeds 25%"],
    [20, "Tech sector concentration exceeds 50%"],
    [18, "Crypto allocation exceeds 30% combined weight"],
    [11, "Elevated annual volatility (28.4%)"],
  ],
  dates: [
    "2023-01-03", "2023-03-15", "2023-06-01", "2023-08-15",
    "2023-11-01", "2024-01-15", "2024-04-01", "2024-07-01",
    "2024-10-01", "2024-12-01", "2025-03-01", "2025-06-01",
    "2025-09-01", "2025-11-15",
  ],
  price_series: {
    Portfolio: [100, 106, 114, 111, 119, 128, 134, 142, 138, 149, 156, 162, 158, 168],
    SPY: [100, 103, 108, 107, 112, 118, 122, 127, 125, 132, 136, 140, 139, 145],
  },
  drawdown_series: [
    0, -0.02, -0.05, -0.12, -0.04, 0, -0.08, -0.03, -0.16, -0.06, 0, -0.04, -0.11, -0.02
  ],
  correlation_matrix: {
    columns: ["AAPL", "NVDA", "ETH-USD", "BTC-USD", "USDC"],
    data: [
      [1.00, 0.72, 0.38, 0.41, 0.01],
      [0.72, 1.00, 0.45, 0.49, -0.02],
      [0.38, 0.45, 1.00, 0.84, 0.00],
      [0.41, 0.49, 0.84, 1.00, 0.00],
      [0.01, -0.02, 0.00, 0.00, 1.00],
    ],
  },
  concentration: {
    top_asset: "AAPL",
    top_weight: 0.35,
    top3_weight: 0.80,
    hhi: 0.2475,
    effective_assets: 4.04,
  },
  volatility: 0.284,
  max_drawdown: -0.384,
  sector_exposure: {
    Technology: 0.60,
    Crypto: 0.35,
    Cash: 0.05,
  },
  correlated_pairs: [
    ["ETH-USD", "BTC-USD", 0.84],
    ["AAPL", "NVDA", 0.72],
    ["NVDA", "ETH-USD", 0.45],
  ],
  stress: {
    "2008 Financial Crisis": -0.428,
    "2020 COVID Crash": -0.294,
    "2022 Fed Hikes": -0.342,
    "Crypto Winter 2022": -0.518,
    "Tech Selloff -10%": -0.089,
    "Yield Spike +100bps": -0.056,
  },
  worst_historical_periods: {
    worst_day: -0.082,
    worst_month: -0.214,
  },
  disclaimer: "Deterministic mathematical model based on historical returns. Not investment advice.",
};

export const MOCK_RISK_DATA = BASE_PORTFOLIO_ANALYSIS;

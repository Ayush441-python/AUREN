import { RiskAnalysis } from "./types";

export const BASE_PORTFOLIO_ANALYSIS: RiskAnalysis = {
  score: 65,
  level: "High",
  normalized_weights: {
    AAPL: 0.35,
    NVDA: 0.25,
    "ETH-USD": 0.20,
    "BTC-USD": 0.15,
    USDC: 0.05,
  },
  reasons: [
    "Largest holding is 35% (over 30%)",
    "Worst past fall was -38% (deeper than -30%)",
    "2 pairs of assets move closely together",
    "60% sits in one sector",
  ],
  hits: [
    [20, "Largest holding is 35% (over 30%)"],
    [15, "Worst past fall was -38% (deeper than -30%)"],
    [15, "2 pairs of assets move closely together"],
    [15, "60% sits in one sector"],
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
    0, -0.02, -0.05, -0.12, -0.04, 0, -0.08, -0.03, -0.16, -0.06, 0, -0.04, -0.11, -0.02,
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
    hhi: 0.25,
    effective_assets: 4.0,
  },
  volatility: 0.284,
  max_drawdown: -0.384,
  sector_exposure: {
    "Big Tech": 0.60,
    Crypto: 0.35,
    "Cash & Stablecoins": 0.05,
  },
  correlated_pairs: [
    ["AAPL", "NVDA", 0.72],
    ["ETH-USD", "BTC-USD", 0.84],
  ],
  stress: {
    "Big Tech falls 20%": -0.12,
    "Chip selloff (semis fall 25%)": -0.0625,
    "NVDA falls 15%": -0.0375,
    "Crypto crash 40%": -0.14,
    "Broad selloff": -0.195,
  },
  worst_historical_periods: {
    worst_day: -0.072,
    worst_month: -0.185,
  },
  disclaimer: "Analytics only, not investment advice. Past data does not predict the future.",
};

export interface SavedPortfolioEntry {
  id: string;
  name: string;
  description: string;
  created: string;
  riskScore: number;
  assets: number;
  weights: Record<string, number>;
}

export const SAVED_PORTFOLIOS: readonly SavedPortfolioEntry[] = [
  {
    id: "p-balanced-01",
    name: "Global Balanced 60/40",
    description: "Equities, aggregate treasuries, gold hedge",
    created: "2026-11-20",
    riskScore: 42,
    assets: 6,
    weights: {
      SPY: 0.3,
      QQQ: 0.2,
      VTI: 0.1,
      TLT: 0.2,
      BND: 0.1,
      GLD: 0.1,
    },
  },
  {
    id: "p-tech-tilt",
    name: "AI & Semiconductor Overweight",
    description: "High growth momentum factor allocation",
    created: "2026-11-24",
    riskScore: 78,
    assets: 8,
    weights: {
      NVDA: 0.22,
      AMD: 0.14,
      AVGO: 0.14,
      TSM: 0.12,
      ASML: 0.1,
      MSFT: 0.12,
      GOOGL: 0.08,
      AAPL: 0.08,
    },
  },
  {
    id: "p-all-weather",
    name: "Bridgewater Style All-Weather",
    description: "Risk parity across macroeconomic environments",
    created: "2026-11-15",
    riskScore: 28,
    assets: 9,
    weights: {
      SPY: 0.2,
      TLT: 0.25,
      BND: 0.15,
      GLD: 0.1,
      SLV: 0.05,
      XLE: 0.08,
      XLF: 0.07,
      JNJ: 0.05,
      PG: 0.05,
    },
  },
];

export function resolveSavedPortfolio(id?: string): SavedPortfolioEntry | undefined {
  if (!id) return undefined;
  return SAVED_PORTFOLIOS.find((entry) => entry.id === id);
}

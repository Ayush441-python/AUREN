export interface PresetPortfolio {
  name: string;
  description: string;
  holdings: [string, number][];
}

export interface QuickWorkspace {
  name: string;
  badge: string;
  weights: Record<string, number>;
}

export const QUICK_WORKSPACES: QuickWorkspace[] = [
  {
    name: "Balanced Multi-Asset",
    badge: "5 assets",
    weights: { AAPL: 0.35, NVDA: 0.25, "ETH-USD": 0.2, "BTC-USD": 0.15, USDC: 0.05 },
  },
  {
    name: "Mega-Cap Tech Focus",
    badge: "4 assets",
    weights: { NVDA: 0.35, MSFT: 0.3, AAPL: 0.2, GOOGL: 0.15 },
  },
  {
    name: "Digital Asset Core",
    badge: "Crypto L1s",
    weights: { "BTC-USD": 0.5, "ETH-USD": 0.35, USDC: 0.15 },
  },
];

export const PRESETS: Record<string, PresetPortfolio> = {
  "Balanced Tech & Crypto": {
    name: "Balanced Tech & Crypto",
    description: "Core AI and cloud holdings paired with blue-chip cryptocurrency",
    holdings: [
      ["NVDA", 40],
      ["MSFT", 30],
      ["GOOGL", 20],
      ["ETH-USD", 10],
    ],
  },
  "Magnificent 7 Tech Heavy": {
    name: "Magnificent 7 Tech Heavy",
    description: "Concentrated exposure across leading US technology giants",
    holdings: [
      ["NVDA", 25],
      ["MSFT", 20],
      ["AAPL", 20],
      ["AMZN", 15],
      ["GOOGL", 10],
      ["META", 10],
    ],
  },
  "Diversified All-Weather": {
    name: "Diversified All-Weather",
    description: "Cross-sector mix across enterprise software, banks, retail, gold, and crypto",
    holdings: [
      ["MSFT", 20],
      ["JPM", 20],
      ["COST", 20],
      ["GLD", 20],
      ["BTC-USD", 10],
      ["ETH-USD", 10],
    ],
  },
  "High Conviction Semiconductor": {
    name: "High Conviction Semiconductor",
    description: "Semiconductor value chain from chip designers to foundries and lithography",
    holdings: [
      ["NVDA", 50],
      ["TSM", 25],
      ["ASML", 15],
      ["AMD", 10],
    ],
  },
  "Institutional Multi-Asset ETF": {
    name: "Institutional Multi-Asset ETF",
    description: "Macro index exposure combined with long-term treasury bonds and gold",
    holdings: [
      ["SPY", 40],
      ["QQQ", 30],
      ["TLT", 20],
      ["GLD", 10],
    ],
  },
};

export function findPresetWeights(name?: string): { name: string; weights: Record<string, number> } | null {
  if (!name) return null;
  const quick = QUICK_WORKSPACES.find((ws) => ws.name === name);
  if (quick) {
    return { name: quick.name, weights: quick.weights };
  }
  const preset = PRESETS[name] ?? Object.values(PRESETS).find((p) => p.name === name);
  if (!preset) return null;
  const total = preset.holdings.reduce((sum, [, weight]) => sum + weight, 0) || 1;
  const weights: Record<string, number> = {};
  preset.holdings.forEach(([ticker, weight]) => {
    weights[ticker] = weight / total;
  });
  return { name: preset.name, weights };
}

export const DEFAULT_PRESET_KEY = "Balanced Tech & Crypto";

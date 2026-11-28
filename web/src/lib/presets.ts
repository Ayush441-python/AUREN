export interface PresetPortfolio {
  name: string;
  description: string;
  holdings: [string, number][];
}

export const BASE_STOCKS_DEMO_PRESET: PresetPortfolio = {
  name: "Base Tokenized Stocks & RWA Demo",
  description: "Coinbase B20 tokenized equities (NVDAc, AAPLc, COINc) paired with Base ETH, cbBTC, and USDC",
  holdings: [
    ["NVDA", 30],
    ["AAPL", 20],
    ["COIN", 15],
    ["ETH-USD", 15],
    ["BTC-USD", 10],
    ["USDC", 10],
  ],
};

export const PRESETS: Record<string, PresetPortfolio> = {
  "Base Tokenized Stocks & RWA Demo": BASE_STOCKS_DEMO_PRESET,
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

export const DEFAULT_PRESET_KEY = "Balanced Tech & Crypto";

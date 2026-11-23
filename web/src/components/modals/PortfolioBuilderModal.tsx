"use client";

import React, { useState } from "react";
import { X, Wallet, Plus, Trash2, ArrowRight, Loader2, Sparkles, Check } from "lucide-react";
import { inspectWallet } from "@/lib/api";

interface PortfolioBuilderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onApplyPortfolio: (holdings: Record<string, number>, name: string) => void;
}

const PRESET_PORTFOLIOS: {
  name: string;
  description: string;
  weights: Record<string, number>;
}[] = [
  {
    name: "Balanced Multi-Asset (Standard)",
    description: "Institutional 60/40 evolution incorporating liquid digital assets.",
    weights: { AAPL: 0.35, NVDA: 0.25, "ETH-USD": 0.20, "BTC-USD": 0.15, USDC: 0.05 },
  },
  {
    name: "Mega-Cap Tech Focus",
    description: "High beta exposure concentrated in top semiconductor & platform equities.",
    weights: { NVDA: 0.35, MSFT: 0.30, AAPL: 0.20, GOOGL: 0.15 },
  },
  {
    name: "Digital Asset Core",
    description: "Institutional crypto allocation with liquid stablecoin reserve.",
    weights: { "BTC-USD": 0.50, "ETH-USD": 0.35, USDC: 0.15 },
  },
  {
    name: "Macro Defensive Reserve",
    description: "Capital preservation model balancing index ETFs and cash equivalents.",
    weights: { SPY: 0.40, GLD: 0.30, QQQ: 0.20, USDC: 0.10 },
  },
];

export function PortfolioBuilderModal({
  isOpen,
  onClose,
  onApplyPortfolio,
}: PortfolioBuilderModalProps) {
  const [tab, setTab] = useState<"presets" | "wallet" | "custom">("presets");
  const [walletAddress, setWalletAddress] = useState("");
  const [walletLoading, setWalletLoading] = useState(false);
  const [walletError, setWalletError] = useState<string | null>(null);

  // Custom asset rows
  const [customAssets, setCustomAssets] = useState<{ ticker: string; weight: number }[]>([
    { ticker: "AAPL", weight: 40 },
    { ticker: "NVDA", weight: 30 },
    { ticker: "BTC-USD", weight: 30 },
  ]);
  const [newTicker, setNewTicker] = useState("");

  if (!isOpen) return null;

  const handleWalletInspect = async () => {
    if (!walletAddress.trim()) {
      setWalletError("Please provide a valid Base wallet address.");
      return;
    }

    setWalletLoading(true);
    setWalletError(null);

    try {
      const res = await inspectWallet(walletAddress.trim());
      if (res.has_holdings && Object.keys(res.portfolio).length > 0) {
        onApplyPortfolio(res.portfolio, `Base Wallet (${walletAddress.slice(0, 6)}...${walletAddress.slice(-4)})`);
        onClose();
      } else {
        setWalletError(
          res.message || "No supported assets detected. Loaded sample starter portfolio instead."
        );
      }
    } catch (err: any) {
      setWalletError(err.message || "Failed to inspect on-chain wallet.");
    } finally {
      setWalletLoading(false);
    }
  };

  const handleApplyCustom = () => {
    const total = customAssets.reduce((sum, item) => sum + item.weight, 0);
    if (total <= 0) return;

    const normalized: Record<string, number> = {};
    customAssets.forEach((item) => {
      if (item.ticker.trim()) {
        normalized[item.ticker.trim().toUpperCase()] = item.weight / total;
      }
    });

    onApplyPortfolio(normalized, "Custom Allocation");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="flex w-full max-w-2xl flex-col rounded-xl border border-[#26262C] bg-[#151518] shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#26262C] px-6 py-4">
          <div>
            <h2 className="text-base font-semibold text-[#F5F6F7]">Load Portfolio Workspace</h2>
            <p className="text-xs text-[#A1A4AB]">Select an institutional preset, inspect Base wallet, or build manually.</p>
          </div>
          <button onClick={onClose} className="rounded-md p-1.5 text-[#A1A4AB] hover:bg-[#1C1C21] hover:text-[#F5F6F7]">
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Mode Selector Tabs */}
        <div className="grid grid-cols-3 border-b border-[#26262C] bg-[#1C1C21]/60 text-xs font-medium">
          <button
            onClick={() => setTab("presets")}
            className={`py-3 text-center transition-colors ${
              tab === "presets"
                ? "border-b-2 border-[#E3B341] text-[#F5F6F7] bg-[#151518]"
                : "text-[#A1A4AB] hover:text-[#F5F6F7]"
            }`}
          >
            Institutional Presets
          </button>
          <button
            onClick={() => setTab("wallet")}
            className={`py-3 text-center transition-colors ${
              tab === "wallet"
                ? "border-b-2 border-[#E3B341] text-[#F5F6F7] bg-[#151518]"
                : "text-[#A1A4AB] hover:text-[#F5F6F7]"
            }`}
          >
            Base L2 Wallet
          </button>
          <button
            onClick={() => setTab("custom")}
            className={`py-3 text-center transition-colors ${
              tab === "custom"
                ? "border-b-2 border-[#E3B341] text-[#F5F6F7] bg-[#151518]"
                : "text-[#A1A4AB] hover:text-[#F5F6F7]"
            }`}
          >
            Custom Allocator
          </button>
        </div>

        {/* Tab Contents */}
        <div className="p-6">
          {tab === "presets" && (
            <div className="space-y-3">
              {PRESET_PORTFOLIOS.map((preset) => (
                <button
                  type="button"
                  key={preset.name}
                  onClick={() => {
                    onApplyPortfolio(preset.weights, preset.name);
                    onClose();
                  }}
                  className="group flex w-full items-center justify-between rounded-lg border border-[#26262C] bg-[#1C1C21] p-4 transition hover:border-[#E3B341] hover:bg-[#202026] cursor-pointer text-left focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#E3B341]"
                >
                  <span>
                    <span className="block text-sm font-semibold text-[#F5F6F7] group-hover:text-[#E3B341]">
                      {preset.name}
                    </span>
                    <span className="block text-xs text-[#A1A4AB] mt-0.5">{preset.description}</span>
                    <span className="mt-2 flex flex-wrap gap-1.5 font-mono text-[11px] text-[#6B6E76]">
                      {Object.entries(preset.weights).map(([ticker, weight]) => (
                        <span key={ticker} className="rounded bg-[#0E0E10] px-1.5 py-0.5 border border-[#26262C]">
                          {ticker}: {(weight * 100).toFixed(0)}%
                        </span>
                      ))}
                    </span>
                  </span>
                  <ArrowRight className="h-4 w-4 text-[#6B6E76] group-hover:text-[#E3B341]" />
                </button>
              ))}
            </div>
          )}

          {tab === "wallet" && (
            <div className="space-y-4">
              <p className="text-xs text-[#A1A4AB]">
                Enter any public Base EVM address. The engine automatically checks tokenized stocks, native Base ETH, cbBTC, and USDC via our multi-RPC pool.
              </p>

              <div>
                <label className="text-xs font-medium text-[#A1A4AB] block mb-1.5">
                  Base EVM Address
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="0x..."
                    value={walletAddress}
                    onChange={(e) => setWalletAddress(e.target.value)}
                    className="flex-1 rounded-md border border-[#26262C] bg-[#0E0E10] px-3 py-2 font-mono text-xs text-[#F5F6F7] placeholder-[#6B6E76] focus:border-[#E3B341] focus:outline-hidden"
                  />
                  <button
                    onClick={handleWalletInspect}
                    disabled={walletLoading}
                    className="flex items-center gap-2 rounded-md bg-[#E3B341] px-4 py-2 text-xs font-semibold text-[#0E0E10] hover:bg-[#f0c254] disabled:opacity-50"
                  >
                    {walletLoading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                    <span>Inspect</span>
                  </button>
                </div>
              </div>

              {walletError && (
                <div className="rounded-md border border-[#E07A5F]/30 bg-[#E07A5F]/10 p-3 text-xs text-[#E07A5F]">
                  {walletError}
                </div>
              )}
            </div>
          )}

          {tab === "custom" && (
            <div className="space-y-4">
              <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                {customAssets.map((asset, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <input
                      type="text"
                      value={asset.ticker}
                      onChange={(e) => {
                        const copy = [...customAssets];
                        copy[i].ticker = e.target.value.toUpperCase();
                        setCustomAssets(copy);
                      }}
                      className="w-32 rounded-md border border-[#26262C] bg-[#0E0E10] px-2.5 py-1.5 font-mono text-xs text-[#F5F6F7]"
                      placeholder="Ticker"
                    />
                    <input
                      type="number"
                      value={asset.weight}
                      onChange={(e) => {
                        const copy = [...customAssets];
                        copy[i].weight = Number(e.target.value);
                        setCustomAssets(copy);
                      }}
                      className="w-24 rounded-md border border-[#26262C] bg-[#0E0E10] px-2.5 py-1.5 font-mono text-xs text-[#F5F6F7]"
                      placeholder="Weight"
                    />
                    <span className="text-xs text-[#6B6E76] font-mono">%</span>
                    <button
                      onClick={() => {
                        setCustomAssets(customAssets.filter((_, idx) => idx !== i));
                      }}
                      className="p-1.5 text-[#6B6E76] hover:text-[#E07A5F]"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>

              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Add ticker (e.g. TSLA, SOL-USD, SPY)"
                  value={newTicker}
                  onChange={(e) => setNewTicker(e.target.value)}
                  className="flex-1 rounded-md border border-[#26262C] bg-[#0E0E10] px-3 py-1.5 font-mono text-xs text-[#F5F6F7]"
                />
                <button
                  onClick={() => {
                    if (newTicker.trim()) {
                      setCustomAssets([...customAssets, { ticker: newTicker.trim().toUpperCase(), weight: 10 }]);
                      setNewTicker("");
                    }
                  }}
                  className="rounded-md border border-[#26262C] bg-[#1C1C21] px-3 py-1.5 text-xs font-medium text-[#F5F6F7] hover:bg-[#26262C]"
                >
                  <Plus className="h-3.5 w-3.5" />
                </button>
              </div>

              <div className="flex justify-end pt-3 border-t border-[#26262C]">
                <button
                  onClick={handleApplyCustom}
                  className="rounded-md bg-[#E3B341] px-4 py-2 text-xs font-semibold text-[#0E0E10] hover:bg-[#f0c254]"
                >
                  Analyze Custom Portfolio
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

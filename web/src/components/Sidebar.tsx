"use client";

import React, { useState } from "react";
import { Plus, Trash2, Wallet, RefreshCw, ArrowRight, Sparkles, Scale } from "lucide-react";
import { PRESETS } from "@/lib/presets";
import { inspectWallet } from "@/lib/api";

interface Props {
  holdings: [string, number][];
  portfolioSize: number;
  supportedTickers: string[];
  isAnalyzing: boolean;
  onHoldingsChange: (holdings: [string, number][]) => void;
  onPortfolioSizeChange: (size: number) => void;
  onRunAnalysis: () => void;
  onWalletImported: (holdings: [string, number][], totalValue: number) => void;
}

export function Sidebar({
  holdings,
  portfolioSize,
  supportedTickers,
  isAnalyzing,
  onHoldingsChange,
  onPortfolioSizeChange,
  onRunAnalysis,
  onWalletImported,
}: Props) {
  const [selectedPreset, setSelectedPreset] = useState<string>("Balanced Tech & Crypto");
  const [walletAddress, setWalletAddress] = useState<string>("");
  const [isWalletLoading, setIsWalletLoading] = useState<boolean>(false);
  const [walletMsg, setWalletMsg] = useState<{ type: "success" | "error" | "warn"; text: string } | null>(null);
  const [isWalletOpen, setIsWalletOpen] = useState<boolean>(false);

  const totalWeight = holdings.reduce((sum, [_, w]) => sum + w, 0);
  const isTotal100 = Math.abs(totalWeight - 100) < 0.05;

  const handlePresetSelect = (name: string) => {
    setSelectedPreset(name);
    if (PRESETS[name]) {
      onHoldingsChange(PRESETS[name].holdings);
    }
  };

  const handleAddHolding = () => {
    const nextTicker = supportedTickers.find(t => !holdings.some(([existing]) => existing === t)) || "NVDA";
    onHoldingsChange([...holdings, [nextTicker, 10]]);
    setSelectedPreset("Custom");
  };

  const handleUpdateHolding = (idx: number, ticker: string, weight: number) => {
    const updated = [...holdings];
    updated[idx] = [ticker.toUpperCase().trim(), isNaN(weight) ? 0 : weight];
    onHoldingsChange(updated);
    setSelectedPreset("Custom");
  };

  const handleRemoveHolding = (idx: number) => {
    if (holdings.length <= 1) return;
    onHoldingsChange(holdings.filter((_, i) => i !== idx));
    setSelectedPreset("Custom");
  };

  const handleNormalizeWeights = () => {
    if (totalWeight <= 0) return;
    const scaled: [string, number][] = holdings.map(([t, w]) => [
      t,
      parseFloat(((w / totalWeight) * 100).toFixed(1)),
    ]);
    onHoldingsChange(scaled);
  };

  const handleEqualWeight = () => {
    if (holdings.length === 0) return;
    const equal = parseFloat((100 / holdings.length).toFixed(1));
    const balanced: [string, number][] = holdings.map(([t]) => [t, equal]);
    onHoldingsChange(balanced);
  };

  const handleImportWallet = async () => {
    if (!walletAddress.trim() || !/^0x[a-fA-F0-9]{40}$/.test(walletAddress.trim())) {
      setWalletMsg({ type: "error", text: "Enter a valid 42-char Base address (0x...)." });
      return;
    }
    setIsWalletLoading(true);
    setWalletMsg(null);

    try {
      const res = await inspectWallet(walletAddress.trim());
      const entries = Object.entries(res.portfolio || {});
      if (!entries.length) {
        setWalletMsg({
          type: "warn",
          text: res.message || "No supported assets or tokenized stocks found in this address.",
        });
        setIsWalletLoading(false);
        return;
      }

      const newHoldings: [string, number][] = entries.map(([t, w]) => [t, parseFloat((w * 100).toFixed(1))]);
      onHoldingsChange(newHoldings);
      if (res.total_value > 0) {
        onPortfolioSizeChange(Math.round(res.total_value));
      }
      setWalletMsg({
        type: "success",
        text: `Loaded ${entries.length} on-chain asset${entries.length > 1 ? "s" : ""} ($${Math.round(res.total_value).toLocaleString()}).`,
      });
      onWalletImported(newHoldings, res.total_value);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Could not query Base nodes.";
      setWalletMsg({ type: "error", text: message });
    } finally {
      setIsWalletLoading(false);
    }
  };

  return (
    <aside className="w-full lg:w-[360px] flex-shrink-0 border-r border-white/[0.08] bg-[#090c13]/95 p-5 flex flex-col justify-between overflow-y-auto">
      <div className="space-y-6">
        {/* Preset Selector Styled as Segment Pills */}
        <div>
          <label className="block text-[11px] font-bold uppercase tracking-wider text-zinc-400 mb-2">
            Preset Allocations
          </label>
          <div className="grid grid-cols-2 gap-1.5 p-1 rounded-xl bg-[#121622] border border-white/[0.06]">
            {Object.keys(PRESETS).slice(0, 4).map((p) => (
              <button
                key={p}
                onClick={() => handlePresetSelect(p)}
                className={`text-[11px] font-semibold py-1.5 px-2.5 rounded-lg truncate transition-all text-left ${
                  selectedPreset === p
                    ? "bg-[#1c2333] text-[#f5b838] border border-[#f5b838]/30 shadow-sm"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {p.split(" ")[0]}
              </button>
            ))}
          </div>
        </div>

        {/* Dynamic Holdings Allocator (Zeus Order-Entry Style) */}
        <div>
          <div className="flex items-center justify-between mb-2.5">
            <label className="text-[11px] font-bold uppercase tracking-wider text-zinc-300">
              Holdings ({holdings.length})
            </label>
            <div className="flex items-center gap-2">
              <button
                onClick={handleEqualWeight}
                className="flex items-center gap-1 text-[11px] font-medium text-zinc-400 hover:text-zinc-200 transition-colors"
                title="Equally split weights"
              >
                <Scale className="w-3 h-3" />
                <span>Equal</span>
              </button>
              <button
                onClick={handleAddHolding}
                className="flex items-center gap-1 text-xs font-bold text-[#f5b838] hover:text-[#ffd269] transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Asset</span>
              </button>
            </div>
          </div>

          <datalist id="ticker-suggestions">
            {supportedTickers.map((t) => (
              <option key={t} value={t} />
            ))}
          </datalist>

          <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
            {holdings.map(([ticker, weight], idx) => {
              const holdingDollars = portfolioSize * ((weight || 0) / 100);
              return (
                <div
                  key={idx}
                  className="bg-[#10141e]/90 border border-white/[0.06] rounded-xl p-2.5 hover:border-white/[0.14] transition-all space-y-1.5"
                >
                  <div className="flex items-center gap-2">
                    {/* Ticker Input */}
                    <input
                      type="text"
                      list="ticker-suggestions"
                      value={ticker}
                      onChange={(e) => handleUpdateHolding(idx, e.target.value, weight)}
                      placeholder="TICKER"
                      className="w-24 text-xs font-mono font-black uppercase bg-[#161c28] border border-white/[0.08] rounded-lg px-2.5 py-1.5 text-zinc-100 focus:border-[#f5b838] focus:outline-none text-center tracking-wider"
                    />

                    {/* Weight Input */}
                    <div className="relative flex-1">
                      <input
                        type="number"
                        value={weight === 0 ? "" : weight}
                        onChange={(e) =>
                          handleUpdateHolding(idx, ticker, parseFloat(e.target.value))
                        }
                        min="0"
                        max="100"
                        step="0.5"
                        placeholder="0"
                        className="w-full text-xs font-mono font-bold text-right bg-[#161c28] border border-white/[0.08] rounded-lg pl-2 pr-6 py-1.5 text-zinc-100 focus:border-[#f5b838] focus:outline-none tabular-nums"
                      />
                      <span className="absolute right-2 top-1.5 text-xs text-zinc-400 font-mono">
                        %
                      </span>
                    </div>

                    {/* Dollar Preview */}
                    <span className="text-[11px] font-mono text-zinc-400 w-16 text-right truncate tabular-nums font-medium">
                      ${Math.round(holdingDollars).toLocaleString()}
                    </span>

                    {/* Delete */}
                    <button
                      onClick={() => handleRemoveHolding(idx)}
                      disabled={holdings.length <= 1}
                      className="text-zinc-500 hover:text-rose-400 disabled:opacity-20 p-1 transition-colors"
                      title="Remove asset"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {/* Slider bar for quick visual weight adjustments */}
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="1"
                    value={weight || 0}
                    onChange={(e) =>
                      handleUpdateHolding(idx, ticker, parseFloat(e.target.value))
                    }
                    className="w-full h-1 bg-[#1c2333] rounded-lg appearance-none cursor-pointer accent-[#f5b838]"
                  />
                </div>
              );
            })}
          </div>

          {/* Allocation Total Indicator */}
          <div className="mt-3 flex items-center justify-between p-2.5 rounded-xl border border-white/[0.06] bg-[#121622]">
            <div className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${
                  isTotal100 ? "bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-amber-400"
                }`}
              />
              <span className="text-xs font-mono font-bold text-zinc-200 tabular-nums">
                Total: {totalWeight.toFixed(1)}%
              </span>
            </div>
            {!isTotal100 ? (
              <button
                onClick={handleNormalizeWeights}
                className="text-xs font-bold text-[#f5b838] hover:underline"
              >
                Scale to 100%
              </button>
            ) : (
              <span className="text-[11px] text-emerald-400 font-mono font-medium">100% Balanced</span>
            )}
          </div>
        </div>

        {/* Portfolio Value in USD */}
        <div>
          <label className="block text-[11px] font-bold uppercase tracking-wider text-zinc-400 mb-2">
            Portfolio Capital (USD)
          </label>
          <div className="relative">
            <span className="absolute left-3.5 top-2.5 text-xs text-zinc-400 font-mono">
              $
            </span>
            <input
              type="number"
              value={portfolioSize}
              onChange={(e) =>
                onPortfolioSizeChange(Math.max(100, parseFloat(e.target.value) || 1000))
              }
              step="500"
              min="100"
              className="w-full text-xs font-mono font-bold bg-[#121622] border border-white/[0.08] rounded-xl pl-8 pr-3.5 py-2.5 text-zinc-100 focus:border-[#f5b838] focus:outline-none tabular-nums"
            />
          </div>
        </div>

        {/* Base Wallet Scanner Drawer */}
        <div className="border border-white/[0.08] bg-[#10141e] rounded-xl p-3.5 shadow-sm">
          <button
            onClick={() => setIsWalletOpen(!isWalletOpen)}
            className="w-full flex items-center justify-between text-xs font-bold text-zinc-300 hover:text-white"
          >
            <div className="flex items-center gap-2">
              <Wallet className="w-3.5 h-3.5 text-[#f5b838]" />
              <span>Base On-Chain Scanner</span>
            </div>
            <span className="text-[10px] text-zinc-400">{isWalletOpen ? "Hide" : "Open"}</span>
          </button>

          {isWalletOpen && (
            <div className="mt-3 space-y-2.5 pt-2.5 border-t border-white/[0.06]">
              <input
                type="text"
                placeholder="0x... (Base Address)"
                value={walletAddress}
                onChange={(e) => setWalletAddress(e.target.value)}
                className="w-full text-xs font-mono bg-[#161c28] border border-white/[0.08] rounded-lg px-2.5 py-2 text-zinc-100 placeholder:text-zinc-600 focus:border-[#f5b838] focus:outline-none"
              />
              <button
                onClick={handleImportWallet}
                disabled={isWalletLoading}
                className="w-full flex items-center justify-center gap-1.5 text-xs font-bold px-3 py-2.5 rounded-lg bg-[#182030] text-zinc-200 hover:bg-[#202a40] hover:text-white transition-all disabled:opacity-50 border border-white/[0.06]"
              >
                {isWalletLoading ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#f5b838]" />
                    <span>Scanning Base Nodes...</span>
                  </>
                ) : (
                  <>
                    <span>Scan On-Chain Holdings</span>
                    <ArrowRight className="w-3 h-3" />
                  </>
                )}
              </button>

              {walletMsg && (
                <div
                  className={`text-[11px] p-2 rounded-lg border ${
                    walletMsg.type === "success"
                      ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400"
                      : walletMsg.type === "warn"
                      ? "bg-amber-500/15 border-amber-500/30 text-amber-400"
                      : "bg-rose-500/15 border-rose-500/30 text-rose-400"
                  }`}
                >
                  {walletMsg.text}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Primary Action Button */}
      <div className="mt-6 pt-4 border-t border-white/[0.08]">
        <button
          onClick={onRunAnalysis}
          disabled={isAnalyzing || holdings.length === 0}
          className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-xs font-black uppercase tracking-wider bg-gradient-to-r from-[#f5b838] to-[#ffd269] text-[#07090e] hover:brightness-110 active:scale-[0.99] transition-all disabled:opacity-50 shadow-[0_0_20px_rgba(245,184,56,0.25)]"
        >
          {isAnalyzing ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin text-[#07090e]" />
              <span>Calculating Risk Engine...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>Run Risk Analytics</span>
              <span className="text-[10px] font-mono opacity-60">↵</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}

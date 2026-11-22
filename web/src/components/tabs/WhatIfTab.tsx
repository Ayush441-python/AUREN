"use client";

import React, { useState } from "react";
import { RiskAnalysis } from "@/lib/types";
import { calculateRisk } from "@/lib/api";
import { GitCompare, ArrowRight, Plus, Trash2, RefreshCw } from "lucide-react";

interface Props {
  currentAnalysis: RiskAnalysis;
  currentHoldings: [string, number][];
}

export function WhatIfTab({ currentAnalysis, currentHoldings }: Props) {
  const [altHoldings, setAltHoldings] = useState<[string, number][]>(() => [...currentHoldings]);
  const [altAnalysis, setAltAnalysis] = useState<RiskAnalysis | null>(null);
  const [isComparing, setIsComparing] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleCloneCurrent = () => {
    setAltHoldings([...currentHoldings]);
  };

  const handleAddHolding = () => {
    setAltHoldings([...altHoldings, ["GLD", 10]]);
  };

  const handleUpdateHolding = (idx: number, ticker: string, weight: number) => {
    const updated = [...altHoldings];
    updated[idx] = [ticker.toUpperCase(), isNaN(weight) ? 0 : weight];
    setAltHoldings(updated);
  };

  const handleRemoveHolding = (idx: number) => {
    if (altHoldings.length <= 1) return;
    setAltHoldings(altHoldings.filter((_, i) => i !== idx));
  };

  const handleRunComparison = async () => {
    setIsComparing(true);
    setErrorMsg(null);
    try {
      const weightsObj: Record<string, number> = {};
      altHoldings.forEach(([t, w]) => {
        weightsObj[t] = (weightsObj[t] || 0) + w;
      });
      const res = await calculateRisk(weightsObj);
      setAltAnalysis(res);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to compare what-if portfolio.");
    } finally {
      setIsComparing(false);
    }
  };

  const scoreDiff = altAnalysis ? altAnalysis.score - currentAnalysis.score : null;
  const volDiff = altAnalysis ? altAnalysis.volatility - currentAnalysis.volatility : null;
  const ddDiff = altAnalysis ? altAnalysis.max_drawdown - currentAnalysis.max_drawdown : null;

  return (
    <div className="space-y-6">
      {/* What-If Allocator Box */}
      <div className="rounded-xl border border-[#1f232c] bg-[#111318] p-5">
        <div className="flex items-center justify-between pb-3.5 border-b border-[#1f232c] mb-4">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
              <GitCompare className="w-3.5 h-3.5 text-[#d8af3f]" />
              <span>Simulate Alternative Portfolio</span>
            </h3>
            <p className="text-[11px] text-zinc-400 mt-0.5">
              Adjust weights or add hedge assets (e.g. Gold, Treasuries) to evaluate risk reduction.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCloneCurrent}
              className="text-xs px-2.5 py-1.5 rounded-lg border border-[#1f232c] bg-[#161920] text-zinc-300 hover:text-white"
            >
              Clone Current
            </button>
            <button
              onClick={handleAddHolding}
              className="text-xs px-2.5 py-1.5 rounded-lg border border-[#1f232c] bg-[#161920] text-[#d8af3f] hover:text-[#f0c75c] flex items-center gap-1"
            >
              <Plus className="w-3 h-3" />
              <span>Add Ticker</span>
            </button>
          </div>
        </div>

        {/* Inputs Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2.5 mb-4">
          {altHoldings.map(([ticker, weight], idx) => (
            <div
              key={idx}
              className="flex items-center gap-1.5 bg-[#161920] border border-[#222632] rounded-xl p-2"
            >
              <input
                type="text"
                value={ticker}
                onChange={(e) => handleUpdateHolding(idx, e.target.value, weight)}
                className="w-20 text-xs font-mono font-bold uppercase bg-[#1f232c] rounded px-2 py-1 text-zinc-100"
              />
              <input
                type="number"
                value={weight}
                onChange={(e) => handleUpdateHolding(idx, ticker, parseFloat(e.target.value))}
                className="w-full text-xs font-mono text-right bg-[#1f232c] rounded px-2 py-1 text-zinc-100"
              />
              <button
                onClick={() => handleRemoveHolding(idx)}
                disabled={altHoldings.length <= 1}
                className="text-zinc-400 hover:text-rose-400 p-1"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>

        <button
          onClick={handleRunComparison}
          disabled={isComparing}
          className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider px-4 py-2.5 rounded-xl bg-[#d8af3f] text-[#090a0d] hover:bg-[#e0b94c] transition-colors disabled:opacity-50"
        >
          {isComparing ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Calculating Simulation...</span>
            </>
          ) : (
            <>
              <span>Run Side-by-Side Comparison</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </>
          )}
        </button>

        {errorMsg && (
          <div className="mt-3 text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 p-2.5 rounded-lg">
            {errorMsg}
          </div>
        )}
      </div>

      {/* Comparison Delta Cards */}
      {altAnalysis && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl border border-[#1f232c] bg-[#111318]">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
              Risk Score Delta
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold font-mono text-zinc-100">
                {currentAnalysis.score} ➔ {altAnalysis.score}
              </span>
              <span
                className={`text-xs font-bold font-mono ${
                  scoreDiff! < 0 ? "text-emerald-400" : scoreDiff! > 0 ? "text-rose-400" : "text-zinc-400"
                }`}
              >
                {scoreDiff! > 0 ? `+${scoreDiff}` : scoreDiff} pts
              </span>
            </div>
            <span className="text-[11px] text-zinc-400 mt-1 block">
              {scoreDiff! < 0 ? "Risk lowered" : scoreDiff! > 0 ? "Risk increased" : "Identical risk"}
            </span>
          </div>

          <div className="p-4 rounded-xl border border-[#1f232c] bg-[#111318]">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
              Volatility Delta
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold font-mono text-zinc-100">
                {(currentAnalysis.volatility * 100).toFixed(1)}% ➔ {(altAnalysis.volatility * 100).toFixed(1)}%
              </span>
              <span
                className={`text-xs font-bold font-mono ${
                  volDiff! < 0 ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {volDiff! > 0 ? `+${(volDiff! * 100).toFixed(1)}%` : `${(volDiff! * 100).toFixed(1)}%`}
              </span>
            </div>
            <span className="text-[11px] text-zinc-400 mt-1 block">
              Annualized return fluctuation
            </span>
          </div>

          <div className="p-4 rounded-xl border border-[#1f232c] bg-[#111318]">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-400 block mb-1">
              Max Drawdown Delta
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold font-mono text-zinc-100">
                {(currentAnalysis.max_drawdown * 100).toFixed(1)}% ➔ {(altAnalysis.max_drawdown * 100).toFixed(1)}%
              </span>
            </div>
            <span className="text-[11px] text-zinc-400 mt-1 block">
              Peak-to-trough historical buffer
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

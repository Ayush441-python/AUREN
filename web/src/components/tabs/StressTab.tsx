"use client";

import React, { useState } from "react";
import { RiskAnalysis } from "@/lib/types";
import { AlertTriangle, Sliders, ArrowDownRight, ArrowUpRight, Zap } from "lucide-react";

interface Props {
  analysis: RiskAnalysis;
  portfolioSize: number;
}

export function StressTab({ analysis, portfolioSize }: Props) {
  const { stress, sector_exposure, normalized_weights } = analysis;

  // Custom shocks per sector group
  const [shocks, setShocks] = useState<Record<string, number>>({});

  const sectorGroups = Object.keys(sector_exposure);

  const handleSliderChange = (group: string, val: number) => {
    setShocks((prev) => ({ ...prev, [group]: val }));
  };

  // Compute live custom shock impact
  const customImpact = Object.entries(normalized_weights).reduce((total, [ticker, weight]) => {
    const sector = Object.keys(sector_exposure).find((g) => g.includes(ticker)) || "Other";
    const shock = shocks[sector] ?? 0;
    return total + weight * (shock / 100);
  }, 0);

  const customDollarChange = portfolioSize * customImpact;

  return (
    <div className="space-y-6">
      {/* Preset Macro Shock Scenarios */}
      <div>
        <div className="flex items-center justify-between mb-3.5">
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span>Preset Historical Crisis Simulations</span>
          </h3>
          <span className="text-[11px] font-mono text-zinc-400">
            Simulated portfolio drawdowns under known stress shocks
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {Object.entries(stress).map(([scenario, impact]) => {
            const dollarImpact = portfolioSize * impact;
            const isNegative = impact < 0;

            return (
              <div
                key={scenario}
                className="p-4 rounded-2xl border border-white/[0.08] bg-gradient-to-b from-[#131722] to-[#0e1119] flex flex-col justify-between hover:border-white/[0.16] transition-all shadow-md"
              >
                <div>
                  <span className="text-xs font-bold text-zinc-100 block mb-1">
                    {scenario}
                  </span>
                  <div className="flex items-baseline gap-2 mt-2">
                    <span
                      className={`text-2xl font-black font-mono tabular-nums ${
                        isNegative ? "text-rose-400" : "text-emerald-400"
                      }`}
                    >
                      {(impact * 100).toFixed(1)}%
                    </span>
                    <span className="text-xs font-mono font-medium text-zinc-400 tabular-nums">
                      ${Math.abs(Math.round(dollarImpact)).toLocaleString()}
                    </span>
                  </div>
                </div>
                <div className="text-[11px] text-zinc-400 mt-3 pt-2.5 border-t border-white/[0.06] flex items-center justify-between font-mono">
                  <span>After Shock:</span>
                  <span className="font-bold text-zinc-200">
                    ${Math.round(portfolioSize + dollarImpact).toLocaleString()}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Interactive Custom Shock Simulator (Zeus Style) */}
      <div className="rounded-2xl border border-white/[0.08] bg-[#0f131d] p-6 shadow-xl">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-white/[0.06] gap-4">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-200 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-[#f5b838]" />
              <span>Interactive Macro Shock Sandbox</span>
            </h3>
            <p className="text-[11px] text-zinc-400 mt-0.5">
              Adjust expected sector shocks to calculate tailored tail-risk impact.
            </p>
          </div>

          {/* Realtime Result Pill */}
          <div className="flex items-center gap-4 bg-[#141926] p-2.5 rounded-xl border border-white/[0.08]">
            <div className="text-right">
              <span className="text-[10px] text-zinc-400 block uppercase tracking-wider font-semibold">
                Portfolio Impact
              </span>
              <span
                className={`text-lg font-black font-mono tabular-nums ${
                  customImpact < 0
                    ? "text-rose-400"
                    : customImpact > 0
                    ? "text-emerald-400"
                    : "text-zinc-300"
                }`}
              >
                {customImpact > 0 ? "+" : ""}
                {(customImpact * 100).toFixed(1)}%
              </span>
            </div>
            <div className="text-right pl-4 border-l border-white/[0.08]">
              <span className="text-[10px] text-zinc-400 block uppercase tracking-wider font-semibold">
                Dollar Change
              </span>
              <span className="text-lg font-black font-mono text-zinc-100 tabular-nums">
                {customDollarChange < 0 ? "−" : "+"}$
                {Math.abs(Math.round(customDollarChange)).toLocaleString()}
              </span>
            </div>
          </div>
        </div>

        {/* Sliders Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-5">
          {sectorGroups.map((group) => {
            const val = shocks[group] ?? 0;
            return (
              <div
                key={group}
                className="p-3.5 rounded-xl border border-white/[0.06] bg-[#141824] hover:border-white/[0.12] transition-colors"
              >
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="font-semibold text-zinc-200 truncate pr-2">{group}</span>
                  <span
                    className={`font-mono font-bold tabular-nums text-xs px-2 py-0.5 rounded-md ${
                      val < 0
                        ? "text-rose-400 bg-rose-500/10 border border-rose-500/20"
                        : val > 0
                        ? "text-emerald-400 bg-emerald-500/10 border border-emerald-500/20"
                        : "text-zinc-400 bg-zinc-800/40"
                    }`}
                  >
                    {val > 0 ? "+" : ""}
                    {val}%
                  </span>
                </div>
                <input
                  type="range"
                  min="-50"
                  max="20"
                  step="5"
                  value={val}
                  onChange={(e) => handleSliderChange(group, parseInt(e.target.value))}
                  className="w-full h-1.5 bg-[#1f2638] rounded-lg appearance-none cursor-pointer accent-[#f5b838]"
                />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

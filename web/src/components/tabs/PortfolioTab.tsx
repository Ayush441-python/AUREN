"use client";

import React from "react";
import { RiskAnalysis } from "@/lib/types";
import { TrendingUp, PieChart, Layers, Building2, ShieldCheck, AlertTriangle } from "lucide-react";

interface Props {
  analysis: RiskAnalysis;
  portfolioSize: number;
}

export function PortfolioTab({ analysis, portfolioSize }: Props) {
  const { concentration, sector_exposure, normalized_weights } = analysis;

  const topSector = Object.entries(sector_exposure).sort((a, b) => b[1] - a[1])[0] || ["Other", 0];

  return (
    <div className="space-y-6">
      {/* 4 Core Financial KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1 */}
        <div className="p-5 rounded-2xl border border-[#222734] bg-gradient-to-b from-[#141720] to-[#0e1015]">
          <div className="flex items-center justify-between text-zinc-400 mb-2.5">
            <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">
              Total Capital
            </span>
            <TrendingUp className="w-4 h-4 text-zinc-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-zinc-100">
            ${Math.round(portfolioSize).toLocaleString()}
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">Portfolio size (USD)</div>
        </div>

        {/* KPI 2 */}
        <div className="p-5 rounded-2xl border border-[#222734] bg-gradient-to-b from-[#141720] to-[#0e1015]">
          <div className="flex items-center justify-between text-zinc-400 mb-2.5">
            <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">
              Largest Position
            </span>
            <PieChart className="w-4 h-4 text-zinc-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-zinc-100">
            {concentration.top_asset} · {(concentration.top_weight * 100).toFixed(1)}%
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">
            {concentration.top_weight > 0.3 ? (
              <span className="text-rose-400 font-medium">Exceeds 30% concentration rule</span>
            ) : (
              <span className="text-emerald-400 font-medium">Within standard threshold (&lt;30%)</span>
            )}
          </div>
        </div>

        {/* KPI 3 */}
        <div className="p-5 rounded-2xl border border-[#222734] bg-gradient-to-b from-[#141720] to-[#0e1015]">
          <div className="flex items-center justify-between text-zinc-400 mb-2.5">
            <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">
              Effective Assets
            </span>
            <Layers className="w-4 h-4 text-[#d8af3f]" />
          </div>
          <div className="text-2xl font-bold font-mono text-[#d8af3f]">
            {concentration.effective_assets.toFixed(1)}
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">
            Inverse HHI (diversification depth)
          </div>
        </div>

        {/* KPI 4 */}
        <div className="p-5 rounded-2xl border border-[#222734] bg-gradient-to-b from-[#141720] to-[#0e1015]">
          <div className="flex items-center justify-between text-zinc-400 mb-2.5">
            <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">
              Dominant Sector
            </span>
            <Building2 className="w-4 h-4 text-zinc-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-zinc-100">
            {(topSector[1] * 100).toFixed(1)}%
          </div>
          <div className="text-[11px] text-zinc-400 mt-1 truncate">
            {topSector[0]} cluster
          </div>
        </div>
      </div>

      {/* Holdings Breakdown Table */}
      <div className="rounded-2xl border border-[#222734] bg-[#111319] p-6 shadow-md">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#222734]">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-300">
              Allocated Holdings &amp; Capital Distribution
            </h3>
            <p className="text-[11px] text-zinc-400 mt-0.5">
              Exact portfolio weighting normalized to 100% basis.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#222734] text-zinc-400">
                <th className="pb-3 font-semibold uppercase tracking-wider text-[11px]">Asset</th>
                <th className="pb-3 font-semibold uppercase tracking-wider text-[11px] text-right">Weight</th>
                <th className="pb-3 font-semibold uppercase tracking-wider text-[11px] text-right">Market Value</th>
                <th className="pb-3 font-semibold uppercase tracking-wider text-[11px] pl-8">Share of Capital</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#222734]/60">
              {Object.entries(normalized_weights).map(([ticker, weight]) => {
                const dollarValue = portfolioSize * weight;
                const pct = (weight * 100).toFixed(1);
                return (
                  <tr key={ticker} className="hover:bg-[#151922] transition-colors">
                    <td className="py-3.5 font-mono font-bold text-zinc-100 text-sm">
                      {ticker}
                    </td>
                    <td className="py-3.5 text-right font-mono text-zinc-300 font-semibold">
                      {pct}%
                    </td>
                    <td className="py-3.5 text-right font-mono font-bold text-zinc-100">
                      ${Math.round(dollarValue).toLocaleString()}
                    </td>
                    <td className="py-3.5 pl-8 w-1/3">
                      <div className="h-2 w-full rounded-full bg-[#1c212c] overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-[#d8af3f] to-[#e4bc4a] rounded-full"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Sector Exposure Breakdown */}
      <div className="rounded-2xl border border-[#222734] bg-[#111319] p-6 shadow-md">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#222734]">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-300">
              Macro Risk Group Clusters
            </h3>
            <p className="text-[11px] text-zinc-400 mt-0.5">
              Related asset classes grouped to unmask hidden concentration.
            </p>
          </div>
          <span className="text-[11px] font-mono text-zinc-400">
            Dashed boundary marks 50% penalty rule
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {Object.entries(sector_exposure).map(([group, weight]) => {
            const isConcentrated = weight > 0.5;
            return (
              <div
                key={group}
                className={`p-4 rounded-xl border transition-all ${
                  isConcentrated
                    ? "border-amber-500/40 bg-amber-500/10 shadow-sm"
                    : "border-[#222734] bg-[#151821]"
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="font-semibold text-zinc-200">{group}</span>
                  <span className="font-mono font-bold text-[#d8af3f] text-sm">
                    {(weight * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-[#202530] overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      isConcentrated ? "bg-amber-400" : "bg-[#d8af3f]"
                    }`}
                    style={{ width: `${Math.min(100, weight * 100)}%` }}
                  />
                </div>
                {isConcentrated && (
                  <div className="flex items-center gap-1.5 text-[11px] text-amber-400 mt-2 font-medium">
                    <AlertTriangle className="w-3 h-3 flex-shrink-0" />
                    <span>Triggers &gt;50% Sector Rule (+15 pts)</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

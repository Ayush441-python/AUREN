"use client";

import React from "react";
import { LiquidityAnalysis } from "@/lib/types";
import { Droplet, Clock, CheckCircle2, AlertCircle } from "lucide-react";

interface Props {
  liquidity: LiquidityAnalysis | null;
  isLoading: boolean;
}

export function LiquidityTab({ liquidity, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="p-12 text-center rounded-xl border border-[#1f232c] bg-[#111318]">
        <div className="inline-block animate-spin w-6 h-6 border-2 border-[#d8af3f] border-t-transparent rounded-full mb-3" />
        <p className="text-xs text-zinc-400">Loading 30-day ADV and days-to-exit metrics...</p>
      </div>
    );
  }

  if (!liquidity || !liquidity.assets) {
    return (
      <div className="p-8 text-center rounded-xl border border-[#1f232c] bg-[#111318]">
        <p className="text-xs text-zinc-400">Liquidity data is currently unavailable.</p>
      </div>
    );
  }

  const { max_days_to_exit, assets, adv_participation } = liquidity;
  const isHealthy = max_days_to_exit < 1.0;
  const slowestAsset = assets.reduce(
    (max, a) => ((a.days_to_exit ?? 0) > (max.days_to_exit ?? 0) ? a : max),
    assets[0]
  );

  return (
    <div className="space-y-6">
      {/* 3 Liquidity KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl border border-[#1f232c] bg-[#111318]">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">
              Slowest Exit Position
            </span>
            <Clock className="w-3.5 h-3.5 text-[#d8af3f]" />
          </div>
          <div className="text-2xl font-bold font-mono text-zinc-100">
            {max_days_to_exit.toFixed(2)} days
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">
            {slowestAsset ? `${slowestAsset.ticker} liquidation pace` : "–"}
          </div>
        </div>

        <div className="p-4 rounded-xl border border-[#1f232c] bg-[#111318]">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">
              Market Participation Limit
            </span>
            <Droplet className="w-3.5 h-3.5 text-zinc-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-zinc-100">
            {(adv_participation * 100).toFixed(0)}% of ADV
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">
            Conservative order execution cap
          </div>
        </div>

        <div className="p-4 rounded-xl border border-[#1f232c] bg-[#111318]">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">
              Liquidity Health Status
            </span>
            {isHealthy ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            ) : (
              <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
            )}
          </div>
          <div
            className={`text-2xl font-bold font-mono ${
              isHealthy ? "text-emerald-400" : "text-amber-400"
            }`}
          >
            {isHealthy ? "Highly Liquid" : "Constrained"}
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">
            {isHealthy ? "All exits complete in < 1 day" : "Bottleneck holdings present"}
          </div>
        </div>
      </div>

      {/* Asset Liquidity Table */}
      <div className="rounded-xl border border-[#1f232c] bg-[#111318] p-5">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-4">
          Position Days-To-Exit Breakdown
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#1f232c] text-zinc-400">
                <th className="pb-3 font-semibold">Ticker</th>
                <th className="pb-3 font-semibold text-right">Holding Value</th>
                <th className="pb-3 font-semibold text-right">30-Day ADV</th>
                <th className="pb-3 font-semibold text-right">Sellable / Day (10%)</th>
                <th className="pb-3 font-semibold text-right">Days To Exit</th>
                <th className="pb-3 font-semibold text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1f232c]/50">
              {assets.map((asset) => {
                const days = asset.days_to_exit ?? 0;
                const isSlow = days >= 1.0;
                const isInstant = days < 0.1;

                return (
                  <tr key={asset.ticker} className="hover:bg-[#161920] transition-colors">
                    <td className="py-3 font-mono font-bold text-zinc-200">
                      {asset.ticker}
                    </td>
                    <td className="py-3 text-right font-mono text-zinc-100">
                      ${Math.round(asset.holding_value).toLocaleString()}
                    </td>
                    <td className="py-3 text-right font-mono text-zinc-400">
                      {asset.adv ? `$${Math.round(asset.adv).toLocaleString()}` : "–"}
                    </td>
                    <td className="py-3 text-right font-mono text-zinc-400">
                      {asset.adv ? `$${Math.round(asset.adv * 0.1).toLocaleString()}` : "–"}
                    </td>
                    <td className="py-3 text-right font-mono font-bold text-zinc-100">
                      {days > 0 ? days.toFixed(3) : "Instant"}
                    </td>
                    <td className="py-3 text-right">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${
                          isSlow
                            ? "bg-rose-500/10 border-rose-500/20 text-rose-400"
                            : isInstant
                            ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                            : "bg-amber-500/10 border-amber-500/20 text-amber-400"
                        }`}
                      >
                        {isSlow ? "Slow (1+ d)" : isInstant ? "Instant (<0.1 d)" : "Liquid (<1 d)"}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

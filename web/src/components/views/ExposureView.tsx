"use client";

import React from "react";
import { RiskAnalysis } from "@/lib/types";
import { formatPercent, formatNumber } from "@/lib/format";
import { PieChart, Layers, BarChart2, CheckCircle2 } from "lucide-react";

interface ExposureViewProps {
  data: RiskAnalysis;
}

export function ExposureView({ data }: ExposureViewProps) {
  const sortedHoldings = Object.entries(data.normalized_weights).sort(
    (a, b) => b[1] - a[1]
  );

  const sortedSectors = Object.entries(data.sector_exposure).sort(
    (a, b) => b[1] - a[1]
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="border-b border-[#26262C] pb-5">
        <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[#F5F6F7]">
          Factor & Asset Exposure
        </h1>
        <p className="mt-1 text-xs sm:text-sm text-[#A1A4AB]">
          Decomposition of portfolio capital across individual assets, sectors, and concentration metrics.
        </p>
      </div>

      {/* Concentration Summary Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="panel-card p-5">
          <span className="text-xs text-[#A1A4AB] block">Top 3 Holdings Concentration</span>
          <div className="font-mono text-2xl font-semibold text-[#F5F6F7] my-1.5">
            {formatPercent(data.concentration.top3_weight)}
          </div>
          <span className="text-xs text-[#6B6E76]">
            {data.concentration.top3_weight > 0.6
              ? "Exceeds 60.0% diversified threshold"
              : "Within institutional diversification limit"}
          </span>
        </div>

        <div className="panel-card p-5">
          <span className="text-xs text-[#A1A4AB] block">Effective Number of Assets</span>
          <div className="font-mono text-2xl font-semibold text-[#7FB3A6] my-1.5">
            {formatNumber(data.concentration.effective_assets, 1)}
          </div>
          <span className="text-xs text-[#6B6E76]">
            Formula: 1 / HHI (Accounts for weight skew)
          </span>
        </div>

        <div className="panel-card p-5">
          <span className="text-xs text-[#A1A4AB] block">Herfindahl-Hirschman Index (HHI)</span>
          <div className="font-mono text-2xl font-semibold text-[#F5F6F7] my-1.5">
            {formatNumber(data.concentration.hhi, 4)}
          </div>
          <span className="text-xs text-[#6B6E76]">
            {data.concentration.hhi > 0.25 ? "High concentration profile" : "Moderate concentration profile"}
          </span>
        </div>
      </div>

      {/* Main Breakdown: Asset Weights & Sector Allocation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Asset Allocation Table */}
        <div className="panel-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-[#F5F6F7] flex items-center gap-2">
              <Layers className="h-4 w-4 text-[#E3B341]" />
              <span>Asset Allocations</span>
            </h3>
            <span className="font-mono text-xs text-[#6B6E76]">
              {sortedHoldings.length} Assets Total
            </span>
          </div>

          <div className="space-y-3.5">
            {sortedHoldings.map(([ticker, weight]) => (
              <div key={ticker} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-mono font-medium text-[#F5F6F7]">{ticker}</span>
                  <span className="font-mono text-[#F5F6F7]">{formatPercent(weight)}</span>
                </div>
                <div className="h-2 w-full rounded-full bg-[#1C1C21] overflow-hidden">
                  <div
                    className="h-full rounded-full bg-[#E3B341] transition-all duration-300"
                    style={{ width: `${Math.min(100, weight * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sector Exposure Table */}
        <div className="panel-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-[#F5F6F7] flex items-center gap-2">
              <PieChart className="h-4 w-4 text-[#7FB3A6]" />
              <span>Sector & Factor Groups</span>
            </h3>
            <span className="font-mono text-xs text-[#6B6E76]">
              {sortedSectors.length} Sectors
            </span>
          </div>

          <div className="space-y-3.5">
            {sortedSectors.map(([sector, exposure]) => (
              <div key={sector} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-[#F5F6F7]">{sector}</span>
                  <span className="font-mono text-[#F5F6F7]">{formatPercent(exposure)}</span>
                </div>
                <div className="h-2 w-full rounded-full bg-[#1C1C21] overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      exposure > 0.4 ? "bg-[#E07A5F]" : "bg-[#7FB3A6]"
                    }`}
                    style={{ width: `${Math.min(100, exposure * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

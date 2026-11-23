"use client";

import React, { useState } from "react";
import { RiskAnalysis } from "@/lib/types";
import { formatPercent, formatNumber } from "@/lib/format";
import { NumbersUsedDrawer } from "@/components/drawer/NumbersUsedDrawer";
import {
  ShieldAlert,
  Calculator,
  ArrowUpRight,
  ChevronRight,
  TrendingDown,
  Layers,
  PieChart,
  Zap,
} from "lucide-react";

interface OverviewViewProps {
  data: RiskAnalysis;
  onNavigateTab: (tab: "exposure" | "correlation" | "stress" | "report") => void;
}

export function OverviewView({ data, onNavigateTab }: OverviewViewProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Sort primary risk drivers by score impact descending, preserving rule declaration order for ties
  const sortedDrivers: string[] =
    data.hits && data.hits.length > 0
      ? [...data.hits].sort(([pA], [pB]) => pB - pA).map(([_, reason]) => reason)
      : data.reasons;

  // Find the most severe stress test impact
  const worstStressEntry = Object.entries(data.stress).sort((a, b) => a[1] - b[1])[0];

  const getRiskColor = (level: string) => {
    switch (level) {
      case "Low":
        return "text-[#7FB3A6] bg-[#7FB3A6]/10 border-[#7FB3A6]/20";
      case "High":
        return "text-[#E07A5F] bg-[#E07A5F]/10 border-[#E07A5F]/20";
      default:
        return "text-[#E3B341] bg-[#E3B341]/10 border-[#E3B341]/20";
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top Banner & Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#26262C] pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[#F5F6F7]">
              Portfolio Risk Overview
            </h1>
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-semibold font-mono border ${getRiskColor(
                data.level
              )}`}
            >
              {data.level} Risk Profile
            </span>
          </div>
          <p className="mt-1 text-xs sm:text-sm text-[#A1A4AB]">
            Deterministic mathematical analysis across 252 trading sessions.
          </p>
        </div>

        <button
          onClick={() => setDrawerOpen(true)}
          className="flex items-center gap-2 rounded-md border border-[#26262C] bg-[#151518] px-3.5 py-2 text-xs font-medium text-[#F5F6F7] transition hover:bg-[#1C1C21] hover:border-[#383842]"
        >
          <Calculator className="h-3.5 w-3.5 text-[#E3B341]" />
          <span>Audit Numbers & Formulas</span>
        </button>
      </div>

      {/* Hero Grid: The Number is the Hero & Primary Why Card */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: 72px Hero Score */}
        <div className="lg:col-span-5 panel-card p-6 sm:p-8 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs text-[#A1A4AB]">
              <span className="font-semibold uppercase tracking-wider text-[11px] text-[#6B6E76]">
                Aggregate Risk Score
              </span>
              <span className="font-mono text-xs text-[#A1A4AB]">Scale: 0 to 100</span>
            </div>

            {/* 72px JetBrains Mono Hero Number */}
            <div className="my-6 flex items-baseline gap-2">
              <span className="font-mono text-7xl sm:text-8xl font-semibold tracking-tight text-[#F5F6F7]">
                {data.score}
              </span>
              <span className="font-mono text-xl sm:text-2xl text-[#6B6E76]">/ 100</span>
            </div>

            <p className="text-xs sm:text-sm text-[#A1A4AB] leading-relaxed">
              Calculated using strict mathematical penalties on concentration, volatility, tail drawdown, and asset co-movements.
            </p>
          </div>

          <div className="mt-6 pt-5 border-t border-[#26262C] grid grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-[#6B6E76] block">Effective Assets</span>
              <span className="font-mono text-base font-semibold text-[#F5F6F7] mt-0.5 block">
                {formatNumber(data.concentration.effective_assets, 1)} <span className="text-xs text-[#6B6E76] font-normal">assets</span>
              </span>
            </div>
            <div>
              <span className="text-[#6B6E76] block">HHI Concentration</span>
              <span className="font-mono text-base font-semibold text-[#F5F6F7] mt-0.5 block">
                {formatNumber(data.concentration.hhi, 3)}
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Primary Why Card with Rank Badges */}
        <div className="lg:col-span-7 panel-card p-6 sm:p-8 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-semibold text-[#F5F6F7]">
                  Primary Risk Drivers
                </h3>
                <p className="text-xs text-[#A1A4AB] mt-0.5">
                  Ordered by score impact on your total portfolio
                </p>
              </div>
              <span className="font-mono text-[11px] text-[#6B6E76] bg-[#0E0E10] px-2.5 py-1 rounded border border-[#26262C]">
                {sortedDrivers.length} Factors Identified
              </span>
            </div>

            <div className="space-y-3 mt-4">
              {sortedDrivers.map((reason, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3.5 rounded-lg border border-[#26262C] bg-[#1C1C21] p-3.5 text-xs sm:text-sm leading-relaxed"
                >
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-[#E3B341]/10 font-mono text-[11px] font-bold text-[#E3B341] border border-[#E3B341]/20 mt-0.5">
                    {i + 1}
                  </span>
                  <span className="text-[#F5F6F7]">{reason}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-[#26262C] flex items-center justify-between text-xs">
            <span className="text-[#6B6E76]">Verified via Historical Return Covariance</span>
            <button
              onClick={() => onNavigateTab("report")}
              className="flex items-center gap-1 text-[#E3B341] hover:underline font-medium"
            >
              <span>Read AI Audit Narrative</span>
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* 4 Supporting Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Annualized Volatility */}
        <div className="panel-card p-5">
          <div className="flex items-center justify-between text-xs text-[#A1A4AB]">
            <span>Annualized Volatility</span>
            <span className="font-mono text-[10px] text-[#6B6E76]">&sigma; &times; &radic;252</span>
          </div>
          <div className="font-mono text-3xl font-medium text-[#F5F6F7] my-2">
            {formatPercent(data.volatility)}
          </div>
          <p className="text-xs text-[#6B6E76] leading-normal">
            Expected annualized fluctuation standard deviation.
          </p>
        </div>

        {/* Metric 2: Max Historical Drawdown */}
        <div className="panel-card p-5">
          <div className="flex items-center justify-between text-xs text-[#A1A4AB]">
            <span>Max Historical Drawdown</span>
            <span className="font-mono text-[10px] text-[#6B6E76]">Peak-to-Trough</span>
          </div>
          <div className="font-mono text-3xl font-medium text-[#E07A5F] my-2">
            {formatPercent(data.max_drawdown)}
          </div>
          <p className="text-xs text-[#6B6E76] leading-normal">
            Deepest loss experienced during the 252d lookback window.
          </p>
        </div>

        {/* Metric 3: Top Asset Weight */}
        <div className="panel-card p-5">
          <div className="flex items-center justify-between text-xs text-[#A1A4AB]">
            <span>Top Asset Concentration</span>
            <span className="font-mono text-[10px] text-[#6B6E76]">{data.concentration.top_asset}</span>
          </div>
          <div className="font-mono text-3xl font-medium text-[#F5F6F7] my-2">
            {formatPercent(data.concentration.top_weight)}
          </div>
          <p className="text-xs text-[#6B6E76] leading-normal">
            Maximum single asset allocation (recommended cap: 25.0%).
          </p>
        </div>

        {/* Metric 4: Worst Month */}
        <div className="panel-card p-5">
          <div className="flex items-center justify-between text-xs text-[#A1A4AB]">
            <span>Worst Single Month</span>
            <span className="font-mono text-[10px] text-[#6B6E76]">30-Day Window</span>
          </div>
          <div className="font-mono text-3xl font-medium text-[#E07A5F] my-2">
            {formatPercent(data.worst_historical_periods.worst_month)}
          </div>
          <p className="text-xs text-[#6B6E76] leading-normal">
            Maximum negative return over any 30 calendar days.
          </p>
        </div>
      </div>

      {/* Stress Strip */}
      {worstStressEntry && (
        <div className="rounded-lg border border-[#26262C] bg-[#151518] p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-[#E07A5F]/10 text-[#E07A5F] border border-[#E07A5F]/20">
              <TrendingDown className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-[#F5F6F7]">
                  Worst Historical Scenario Impact: {worstStressEntry[0]}
                </span>
                <span className="font-mono text-xs font-semibold text-[#E07A5F]">
                  {formatPercent(worstStressEntry[1])}
                </span>
              </div>
              <p className="text-xs text-[#A1A4AB] mt-0.5">
                Modeled response if a similar macroeconomic shock occurred under current weights.
              </p>
            </div>
          </div>

          <button
            onClick={() => onNavigateTab("stress")}
            className="flex items-center gap-1.5 rounded-md bg-[#1C1C21] px-3 py-1.5 text-xs font-medium text-[#F5F6F7] border border-[#26262C] hover:bg-[#23232A] transition"
          >
            <span>Open Stress Simulator</span>
            <ArrowUpRight className="h-3 w-3 text-[#A1A4AB]" />
          </button>
        </div>
      )}

      {/* Audit Drawer */}
      <NumbersUsedDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        data={data}
      />
    </div>
  );
}

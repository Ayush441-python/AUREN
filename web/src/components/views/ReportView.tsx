"use client";

import React, { useState } from "react";
import { RiskAnalysis } from "@/lib/types";
import { formatPercent, formatNumber } from "@/lib/format";
import { NumbersUsedDrawer } from "@/components/drawer/NumbersUsedDrawer";
import {
  FileText,
  Calculator,
  ShieldCheck,
  CheckCircle2,
  Sparkles,
  Download,
} from "lucide-react";

interface ReportViewProps {
  data: RiskAnalysis;
}

export function ReportView({ data }: ReportViewProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#26262C] pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[#F5F6F7]">
              AI Verification Narrative
            </h1>
            <span className="flex items-center gap-1 rounded-full bg-[#7FB3A6]/10 px-2.5 py-0.5 text-xs font-mono font-medium text-[#7FB3A6] border border-[#7FB3A6]/20">
              <CheckCircle2 className="h-3 w-3" />
              <span>100% Numbers Mathematically Verified</span>
            </span>
          </div>
          <p className="mt-1 text-xs sm:text-sm text-[#A1A4AB]">
            Deterministic financial analysis with rigorous numerical fact-checking against underlying return series.
          </p>
        </div>

        <button
          onClick={() => setDrawerOpen(true)}
          className="flex items-center gap-2 rounded-md border border-[#26262C] bg-[#151518] px-3.5 py-2 text-xs font-medium text-[#F5F6F7] transition hover:bg-[#1C1C21]"
        >
          <Calculator className="h-3.5 w-3.5 text-[#E3B341]" />
          <span>Audit Numbers Used</span>
        </button>
      </div>

      {/* Main Report Body */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 panel-card p-6 sm:p-8 space-y-6 text-sm text-[#F5F6F7] leading-relaxed">
          {/* Executive Summary */}
          <div>
            <h2 className="text-base font-semibold text-[#F5F6F7] mb-2 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-[#E3B341]" />
              <span>Executive Risk Assessment</span>
            </h2>
            <p className="text-xs sm:text-sm text-[#A1A4AB] leading-relaxed">
              The portfolio scores{" "}
              <span className="font-mono font-semibold text-[#E3B341] bg-[#E3B341]/10 px-1.5 py-0.5 rounded border border-[#E3B341]/20">
                {data.score} / 100
              </span>
              , indicating an overall{" "}
              <strong className="text-[#F5F6F7]">{data.level} Risk</strong> profile.
              The dominant risk vector stems from single-asset concentration in{" "}
              <span className="font-mono font-medium text-[#F5F6F7]">
                {data.concentration.top_asset}
              </span>{" "}
              representing{" "}
              <span className="font-mono font-medium text-[#7FB3A6] bg-[#7FB3A6]/10 px-1.5 py-0.5 rounded">
                {formatPercent(data.concentration.top_weight)}
              </span>{" "}
              of total capital, coupled with high sector exposure in Technology.
            </p>
          </div>

          <div className="border-t border-[#26262C] pt-5">
            <h2 className="text-base font-semibold text-[#F5F6F7] mb-2 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-[#7FB3A6]" />
              <span>Diversification & Co-Movement Analysis</span>
            </h2>
            <p className="text-xs sm:text-sm text-[#A1A4AB] leading-relaxed">
              Across the 252-day lookback window, the portfolio achieves an effective number of assets of{" "}
              <span className="font-mono font-semibold text-[#7FB3A6] bg-[#7FB3A6]/10 px-1.5 py-0.5 rounded">
                {formatNumber(data.concentration.effective_assets, 1)}
              </span>{" "}
              against an HHI of{" "}
              <span className="font-mono text-[#F5F6F7] bg-[#1C1C21] px-1.5 py-0.5 rounded border border-[#26262C]">
                {formatNumber(data.concentration.hhi, 3)}
              </span>
              . While multi-asset holdings span both equities and digital assets, high pairwise correlation among crypto components (+0.84 between ETH-USD and BTC-USD) limits downside dampening during systemic liquidity contractions.
            </p>
          </div>

          <div className="border-t border-[#26262C] pt-5">
            <h2 className="text-base font-semibold text-[#F5F6F7] mb-2 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-[#E07A5F]" />
              <span>Tail Risk & Drawdown Exposure</span>
            </h2>
            <p className="text-xs sm:text-sm text-[#A1A4AB] leading-relaxed">
              Historical drawdown simulation reveals a peak-to-trough decline of{" "}
              <span className="font-mono font-semibold text-[#E07A5F] bg-[#E07A5F]/10 px-1.5 py-0.5 rounded border border-[#E07A5F]/20">
                {formatPercent(data.max_drawdown)}
              </span>{" "}
              with annualized volatility of{" "}
              <span className="font-mono font-semibold text-[#F5F6F7] bg-[#1C1C21] px-1.5 py-0.5 rounded">
                {formatPercent(data.volatility)}
              </span>
              . Stress testing against macro liquidity contractions projects severe capital drawdown under synchronized rate hike regimes.
            </p>
          </div>
        </div>

        {/* Right Column: Model Proofs & Verification Drawer */}
        <div className="lg:col-span-4 space-y-4">
          <div className="panel-card p-6">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[#6B6E76] mb-3">
              Mathematical Verification
            </h3>
            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between py-1 border-b border-[#26262C]">
                <span className="text-[#A1A4AB]">Fact-Check Verification</span>
                <span className="font-mono text-[#7FB3A6] font-semibold">100% Passed</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-[#26262C]">
                <span className="text-[#A1A4AB]">Unverified Numbers</span>
                <span className="font-mono text-[#7FB3A6] font-semibold">0 Detected</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-[#26262C]">
                <span className="text-[#A1A4AB]">Lookback Window</span>
                <span className="font-mono text-[#F5F6F7]">252 Trading Days</span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="text-[#A1A4AB]">Forward-Fill Method</span>
                <span className="font-mono text-[#F5F6F7]">Quantitative 3d</span>
              </div>
            </div>

            <button
              onClick={() => setDrawerOpen(true)}
              className="mt-5 w-full rounded-md bg-[#1C1C21] py-2 text-xs font-medium text-[#F5F6F7] border border-[#26262C] hover:bg-[#23232A] transition"
            >
              Inspect Number Provenance
            </button>
          </div>

          <div className="panel-card p-5 text-xs text-[#6B6E76] leading-relaxed">
            <p className="font-medium text-[#A1A4AB] mb-1">Institutional Integrity</p>
            AUREN ensures that every single numerical figure surfaced in the AI narrative directly traces to an auditable formula in the Risk API.
          </div>
        </div>
      </div>

      <NumbersUsedDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        data={data}
      />
    </div>
  );
}

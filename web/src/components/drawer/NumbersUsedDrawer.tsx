"use client";

import React, { useState } from "react";
import { RiskAnalysis } from "@/lib/types";
import { formatPercent, formatNumber } from "@/lib/format";
import { X, Calculator, ShieldCheck, Check, Copy } from "lucide-react";

interface NumbersUsedDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  data: RiskAnalysis;
}

export function NumbersUsedDrawer({ isOpen, onClose, data }: NumbersUsedDrawerProps) {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const rawJson = JSON.stringify(
    {
      deterministic_score: data.score,
      risk_level: data.level,
      covariance_lookback_days: 252,
      concentration_metrics: data.concentration,
      annualized_volatility: data.volatility,
      max_historical_drawdown: data.max_drawdown,
      correlated_pairs: data.correlated_pairs,
      sector_exposures: data.sector_exposure,
      historical_worst: data.worst_historical_periods,
    },
    null,
    2
  );

  const handleCopy = () => {
    navigator.clipboard.writeText(rawJson);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="flex h-full w-full max-w-xl flex-col border-l border-[#26262C] bg-[#151518] p-6 shadow-2xl overflow-y-auto">
        {/* Drawer Header */}
        <div className="flex items-center justify-between border-b border-[#26262C] pb-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-[#E3B341]/10 text-[#E3B341] border border-[#E3B341]/20">
              <Calculator className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-[#F5F6F7]">Audit & Mathematical Verification</h2>
              <p className="text-xs text-[#A1A4AB]">Raw numbers, formulas, and parameters used in scoring</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-[#A1A4AB] hover:bg-[#1C1C21] hover:text-[#F5F6F7]"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Audit Details */}
        <div className="mt-6 space-y-6">
          {/* Integrity Guarantee */}
          <div className="rounded-lg border border-[#26262C] bg-[#1C1C21] p-3.5">
            <div className="flex items-center gap-2 text-xs font-semibold text-[#7FB3A6]">
              <ShieldCheck className="h-4 w-4" />
              <span>Deterministic Rule Proof Guarantee</span>
            </div>
            <p className="mt-1 text-xs text-[#A1A4AB] leading-relaxed">
              Every score is computed strictly using closed-form statistical formulas on 252 trading days of aligned price data.
              No probabilistic models or opaque black-box heuristics are applied.
            </p>
          </div>

          {/* Metric Breakdown Table */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[#6B6E76] mb-2.5">
              Input Vectors & Computed Metrics
            </h3>
            <div className="rounded-lg border border-[#26262C] overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-[#26262C] bg-[#1C1C21] text-[#A1A4AB]">
                  <tr>
                    <th className="px-3.5 py-2 font-medium">Metric</th>
                    <th className="px-3.5 py-2 font-medium text-right">Computed Value</th>
                    <th className="px-3.5 py-2 font-medium">Threshold / Formula</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#26262C] text-[#F5F6F7]">
                  <tr>
                    <td className="px-3.5 py-2 font-medium">Single Asset Conc.</td>
                    <td className="px-3.5 py-2 text-right font-mono text-[#E3B341]">
                      {formatPercent(data.concentration.top_weight)}
                    </td>
                    <td className="px-3.5 py-2 text-[#A1A4AB]">&gt; 25.0% adds penalty</td>
                  </tr>
                  <tr>
                    <td className="px-3.5 py-2 font-medium">Top 3 Combined</td>
                    <td className="px-3.5 py-2 text-right font-mono">
                      {formatPercent(data.concentration.top3_weight)}
                    </td>
                    <td className="px-3.5 py-2 text-[#A1A4AB]">&gt; 60.0% adds penalty</td>
                  </tr>
                  <tr>
                    <td className="px-3.5 py-2 font-medium">HHI Index</td>
                    <td className="px-3.5 py-2 text-right font-mono">
                      {formatNumber(data.concentration.hhi, 4)}
                    </td>
                    <td className="px-3.5 py-2 text-[#A1A4AB]">&Sigma; (w_i)^2 (0 to 1)</td>
                  </tr>
                  <tr>
                    <td className="px-3.5 py-2 font-medium">Effective Assets</td>
                    <td className="px-3.5 py-2 text-right font-mono text-[#7FB3A6]">
                      {formatNumber(data.concentration.effective_assets, 1)}
                    </td>
                    <td className="px-3.5 py-2 text-[#A1A4AB]">1 / HHI</td>
                  </tr>
                  <tr>
                    <td className="px-3.5 py-2 font-medium">Annualized Volatility</td>
                    <td className="px-3.5 py-2 text-right font-mono">
                      {formatPercent(data.volatility)}
                    </td>
                    <td className="px-3.5 py-2 text-[#A1A4AB]">&radic;252 &times; &sigma;_daily</td>
                  </tr>
                  <tr>
                    <td className="px-3.5 py-2 font-medium">Max Drawdown</td>
                    <td className="px-3.5 py-2 text-right font-mono text-[#E07A5F]">
                      {formatPercent(data.max_drawdown)}
                    </td>
                    <td className="px-3.5 py-2 text-[#A1A4AB]">Min (P_t / Peak_t - 1)</td>
                  </tr>
                  <tr>
                    <td className="px-3.5 py-2 font-medium">Max Sector Exposure</td>
                    <td className="px-3.5 py-2 text-right font-mono">
                      {Object.entries(data.sector_exposure).sort((a, b) => b[1] - a[1])[0]
                        ? `${Object.entries(data.sector_exposure).sort((a, b) => b[1] - a[1])[0][0]}: ${formatPercent(Object.entries(data.sector_exposure).sort((a, b) => b[1] - a[1])[0][1])}`
                        : "—"}
                    </td>
                    <td className="px-3.5 py-2 text-[#A1A4AB]">&gt; 40.0% adds penalty</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Raw JSON Payload */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#6B6E76]">
                Exact Machine Output (JSON)
              </span>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 rounded bg-[#1C1C21] px-2 py-1 text-xs text-[#A1A4AB] hover:text-[#F5F6F7] border border-[#26262C]"
              >
                {copied ? <Check className="h-3 w-3 text-[#7FB3A6]" /> : <Copy className="h-3 w-3" />}
                <span>{copied ? "Copied" : "Copy Raw"}</span>
              </button>
            </div>
            <pre className="max-h-60 overflow-y-auto rounded-lg border border-[#26262C] bg-[#0E0E10] p-3 font-mono text-[11px] text-[#A1A4AB] leading-relaxed">
              {rawJson}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

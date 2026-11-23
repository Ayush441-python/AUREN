"use client";

import React, { useState, useEffect } from "react";
import { RiskAnalysis } from "@/lib/types";
import { formatPercent } from "@/lib/format";
import { Activity, Sliders, RotateCcw, AlertTriangle, ShieldCheck } from "lucide-react";

interface StressViewProps {
  data: RiskAnalysis;
  baselineData?: RiskAnalysis;
  onSimulate?: (newWeights: Record<string, number>) => void;
  onReset?: () => void;
}

export function StressView({ data, baselineData, onSimulate, onReset }: StressViewProps) {
  const base = baselineData || data;
  const initialWeights = { ...base.normalized_weights };
  const [weights, setWeights] = useState<Record<string, number>>(initialWeights);

  useEffect(() => {
    setWeights({ ...(baselineData || data).normalized_weights });
  }, [baselineData, data]);

  const handleWeightChange = (ticker: string, newPct: number) => {
    const updated = { ...weights, [ticker]: newPct / 100 };
    setWeights(updated);
  };

  const handleReset = () => {
    const orig = { ...(baselineData || data).normalized_weights };
    setWeights(orig);
    if (onReset) onReset();
  };

  // Compute total weight to display normalization feedback
  const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="border-b border-[#26262C] pb-5">
        <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[#F5F6F7]">
          Stress Scenarios & What-If Sandbox
        </h1>
        <p className="mt-1 text-xs sm:text-sm text-[#A1A4AB]">
          Deterministic shock simulations modeled on actual historical market drawdowns and live capital rebalancing.
        </p>
      </div>

      {/* Historical Stress Scenarios Grid */}
      <div>
        <h3 className="text-sm font-semibold text-[#F5F6F7] flex items-center gap-2 mb-3">
          <Activity className="h-4 w-4 text-[#E3B341]" />
          <span>Historical Macro Scenarios</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(data.stress).map(([scenario, impact]) => (
            <div key={scenario} className="panel-card p-5 flex flex-col justify-between">
              <div>
                <span className="text-xs font-medium text-[#A1A4AB] block">
                  {scenario}
                </span>
                <div className="font-mono text-3xl font-semibold text-[#E07A5F] my-2">
                  {formatPercent(impact)}
                </div>
              </div>
              <p className="text-xs text-[#6B6E76] leading-relaxed mt-2 pt-2 border-t border-[#26262C]">
                Simulated shock on current portfolio weights.
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Interactive What-If Sandbox */}
      <div className="panel-card p-6 mt-8">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-6 pb-4 border-b border-[#26262C]">
          <div>
            <h3 className="text-base font-semibold text-[#F5F6F7] flex items-center gap-2">
              <Sliders className="h-4 w-4 text-[#E3B341]" />
              <span>Interactive What-If Sandbox</span>
            </h3>
            <p className="text-xs text-[#A1A4AB] mt-0.5">
              Adjust position weights to explore how rebalancing alters portfolio risk.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="font-mono text-xs text-[#A1A4AB]">
              Total Weight:{" "}
              <strong
                className={
                  Math.abs(totalWeight - 1.0) < 0.01
                    ? "text-[#7FB3A6]"
                    : "text-[#E3B341]"
                }
              >
                {(totalWeight * 100).toFixed(1)}%
              </strong>
            </span>
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 rounded-md border border-[#26262C] bg-[#1C1C21] px-2.5 py-1 text-xs text-[#A1A4AB] hover:text-[#F5F6F7]"
            >
              <RotateCcw className="h-3 w-3" />
              <span>Reset</span>
            </button>
          </div>
        </div>

        {/* Sliders Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {Object.entries(weights).map(([ticker, weight]) => {
            const pct = Math.round(weight * 100);
            return (
              <div key={ticker} className="space-y-2 rounded-lg bg-[#1C1C21] p-4 border border-[#26262C]">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-mono font-semibold text-[#F5F6F7]">{ticker}</span>
                  <span className="font-mono font-medium text-[#E3B341]">{pct}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="1"
                  value={pct}
                  onChange={(e) => handleWeightChange(ticker, Number(e.target.value))}
                  className="w-full accent-[#E3B341] cursor-pointer"
                />
              </div>
            );
          })}
        </div>

        {onSimulate && (
          <div className="mt-6 flex justify-end">
            <button
              onClick={() => onSimulate(weights)}
              className="rounded-md bg-[#E3B341] px-4 py-2 text-xs font-semibold text-[#0E0E10] transition hover:bg-[#f0c254]"
            >
              Recalculate Stress Matrix with New Weights
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

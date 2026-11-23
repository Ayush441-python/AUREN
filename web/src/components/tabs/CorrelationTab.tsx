"use client";

import React from "react";
import { RiskAnalysis } from "@/lib/types";
import { GitCommit, AlertTriangle, CheckCircle2 } from "lucide-react";

interface Props {
  analysis: RiskAnalysis;
}

export function CorrelationTab({ analysis }: Props) {
  const { correlation_matrix, correlated_pairs } = analysis;
  const { columns, data } = correlation_matrix;

  // Find strongest non-self pair
  let highestPair: { a: string; b: string; val: number } | null = null;
  for (let i = 0; i < columns.length; i++) {
    for (let j = i + 1; j < columns.length; j++) {
      const val = data[i][j];
      if (!highestPair || val > highestPair.val) {
        highestPair = { a: columns[i], b: columns[j], val };
      }
    }
  }

  const getHeatmapColor = (val: number, isDiagonal: boolean) => {
    if (isDiagonal) return "bg-[#1f232c] text-zinc-400 font-bold";
    if (val >= 0.8) return "bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30";
    if (val >= 0.7) return "bg-amber-500/10 text-amber-400 font-semibold";
    if (val <= 0.2) return "bg-emerald-500/10 text-emerald-400 font-medium";
    return "bg-[#14161e] text-zinc-300";
  };

  return (
    <div className="space-y-6">
      {/* 2 Correlation KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="p-4 rounded-xl border border-[#1f232c] bg-[#111318]">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">
              Strongest Asset Pair
            </span>
            <GitCommit className="w-3.5 h-3.5 text-[#d8af3f]" />
          </div>
          <div className="text-2xl font-bold font-mono text-zinc-100">
            {highestPair ? `${highestPair.a} · ${highestPair.b}` : "–"}
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">
            {highestPair ? `Correlation coefficient: r = ${highestPair.val.toFixed(2)}` : "–"}
          </div>
        </div>

        <div className="p-4 rounded-xl border border-[#1f232c] bg-[#111318]">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">
              High Correlation Pairs (r &gt; 0.70)
            </span>
            {correlated_pairs.length >= 2 ? (
              <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
            ) : (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            )}
          </div>
          <div
            className={`text-2xl font-bold font-mono ${
              correlated_pairs.length >= 2 ? "text-rose-400" : "text-emerald-400"
            }`}
          >
            {correlated_pairs.length} pairs
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">
            {correlated_pairs.length >= 2
              ? "Exceeds 2-pair rule threshold (+15 pts)"
              : "Well-decoupled asset movements"}
          </div>
        </div>
      </div>

      {/* Heatmap Matrix */}
      <div className="rounded-xl border border-[#1f232c] bg-[#111318] p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
              Pairwise Pearson Correlation Matrix (r)
            </h3>
            <p className="text-[11px] text-zinc-400 mt-0.5">
              Highlighted cells (r &gt; 0.70) move in close lockstep, offering diminished diversification.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-center text-xs border-collapse">
            <thead>
              <tr>
                <th className="p-2 text-left font-semibold text-zinc-400 border-b border-[#1f232c]">
                  Ticker
                </th>
                {columns.map((col) => (
                  <th
                    key={col}
                    className="p-2 font-mono font-bold text-zinc-300 border-b border-[#1f232c]"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {columns.map((rowTicker, i) => (
                <tr key={rowTicker}>
                  <td className="p-2 text-left font-mono font-bold text-zinc-300 border-b border-[#1f232c]">
                    {rowTicker}
                  </td>
                  {columns.map((colTicker, j) => {
                    const isDiag = i === j;
                    const val = data[i][j];
                    return (
                      <td key={colTicker} className="p-1.5 border-b border-[#1f232c]/50">
                        <div
                          className={`py-2 px-2.5 rounded-lg font-mono text-xs ${getHeatmapColor(
                            val,
                            isDiag
                          )}`}
                        >
                          {val.toFixed(2)}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

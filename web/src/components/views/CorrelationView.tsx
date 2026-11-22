"use client";

import React, { useState } from "react";
import { RiskAnalysis } from "@/lib/types";
import { formatNumber } from "@/lib/format";
import { Grid3X3, AlertTriangle, Info, CheckCircle2 } from "lucide-react";

interface CorrelationViewProps {
  data: RiskAnalysis;
}

export function CorrelationView({ data }: CorrelationViewProps) {
  const matrix = data.correlation_matrix;
  const cols = matrix.columns;
  const [hoveredCell, setHoveredCell] = useState<{
    assetA: string;
    assetB: string;
    value: number;
  } | null>(null);

  const getCellColor = (val: number, isDiagonal: boolean) => {
    if (isDiagonal) return "bg-[#1C1C21] text-[#6B6E76] font-mono";
    if (val >= 0.75) return "bg-[#E07A5F]/25 text-[#E07A5F] font-mono font-semibold";
    if (val >= 0.50) return "bg-[#E3B341]/20 text-[#E3B341] font-mono font-medium";
    if (val <= 0.20) return "bg-[#7FB3A6]/15 text-[#7FB3A6] font-mono";
    return "bg-[#151518] text-[#A1A4AB] font-mono";
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="border-b border-[#26262C] pb-5">
        <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[#F5F6F7]">
          Correlation Matrix & Co-Movement
        </h1>
        <p className="mt-1 text-xs sm:text-sm text-[#A1A4AB]">
          Pairwise correlation coefficients calculated from aligned daily log-returns over 252 sessions.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Heatmap Grid */}
        <div className="lg:col-span-8 panel-card p-6 overflow-x-auto">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-sm font-semibold text-[#F5F6F7] flex items-center gap-2">
              <Grid3X3 className="h-4 w-4 text-[#E3B341]" />
              <span>Pairwise Matrix</span>
            </h3>

            {hoveredCell ? (
              <span className="font-mono text-xs text-[#E3B341] bg-[#1C1C21] px-2.5 py-1 rounded border border-[#26262C]">
                {hoveredCell.assetA} &times; {hoveredCell.assetB}: {formatNumber(hoveredCell.value, 2)}
              </span>
            ) : (
              <span className="text-xs text-[#6B6E76]">Hover over any cell to inspect</span>
            )}
          </div>

          {/* Matrix Table */}
          <div className="inline-block min-w-full">
            <div
              className="grid gap-1.5"
              style={{
                gridTemplateColumns: `auto repeat(${cols.length}, minmax(44px, 1fr))`,
              }}
            >
              {/* Header Corner */}
              <div className="h-9 w-16" />

              {/* Column Headers */}
              {cols.map((col) => (
                <div
                  key={col}
                  className="flex h-9 items-center justify-center font-mono text-[11px] font-semibold text-[#A1A4AB] px-1 truncate"
                  title={col}
                >
                  {col}
                </div>
              ))}

              {/* Matrix Rows */}
              {matrix.data.map((row, rIdx) => {
                const rowTicker = cols[rIdx];
                return (
                  <React.Fragment key={rowTicker}>
                    {/* Row Header */}
                    <div className="flex h-11 items-center font-mono text-[11px] font-semibold text-[#A1A4AB] pr-3 truncate">
                      {rowTicker}
                    </div>

                    {/* Cells */}
                    {row.map((val, cIdx) => {
                      const colTicker = cols[cIdx];
                      const isDiagonal = rIdx === cIdx;

                      return (
                        <div
                          key={`${rowTicker}-${colTicker}`}
                          onMouseEnter={() =>
                            setHoveredCell({
                              assetA: rowTicker,
                              assetB: colTicker,
                              value: val,
                            })
                          }
                          onMouseLeave={() => setHoveredCell(null)}
                          className={`flex h-11 items-center justify-center rounded text-xs transition-colors cursor-pointer border border-[#26262C]/40 ${getCellColor(
                            val,
                            isDiagonal
                          )} hover:border-[#E3B341] hover:scale-105`}
                        >
                          {formatNumber(val, 2)}
                        </div>
                      );
                    })}
                  </React.Fragment>
                );
              })}
            </div>
          </div>

          {/* Legend */}
          <div className="mt-6 pt-4 border-t border-[#26262C] flex flex-wrap items-center gap-4 text-xs text-[#6B6E76]">
            <div className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded bg-[#7FB3A6]/20 border border-[#7FB3A6]/40" />
              <span>Low Correlation (&le; 0.20)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded bg-[#1C1C21] border border-[#26262C]" />
              <span>Moderate (0.21 &ndash; 0.49)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded bg-[#E3B341]/20 border border-[#E3B341]/40" />
              <span>Elevated (0.50 &ndash; 0.74)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded bg-[#E07A5F]/25 border border-[#E07A5F]/40" />
              <span>Severe Co-Movement (&ge; 0.75)</span>
            </div>
          </div>
        </div>

        {/* Right Column: High Co-Movement Pairs */}
        <div className="lg:col-span-4 panel-card p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-[#F5F6F7]">
                Correlated Asset Pairs
              </h3>
              <span className="font-mono text-xs text-[#6B6E76]">
                {data.correlated_pairs.length} Elevated
              </span>
            </div>

            {data.correlated_pairs.length > 0 ? (
              <div className="space-y-3">
                {data.correlated_pairs.map(([assetA, assetB, coef], idx) => (
                  <div
                    key={idx}
                    className="rounded-lg border border-[#26262C] bg-[#1C1C21] p-3 text-xs"
                  >
                    <div className="flex items-center justify-between font-mono">
                      <span className="font-semibold text-[#F5F6F7]">
                        {assetA} &times; {assetB}
                      </span>
                      <span
                        className={`font-semibold ${
                          coef >= 0.75 ? "text-[#E07A5F]" : "text-[#E3B341]"
                        }`}
                      >
                        +{formatNumber(coef, 2)}
                      </span>
                    </div>
                    <p className="mt-1 text-[11px] text-[#A1A4AB] leading-relaxed">
                      {coef >= 0.75
                        ? "Strong synchronized movement. These assets fail to cushion portfolio drawdowns when moving downward together."
                        : "Moderate joint exposure. Offers partial diversification benefits during volatility."}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-lg border border-[#26262C] bg-[#1C1C21] p-4 text-xs text-[#7FB3A6] flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                <span>No pairs exceed the 0.60 high correlation threshold. Portfolio exhibits strong asset independence.</span>
              </div>
            )}
          </div>

          <div className="mt-6 pt-4 border-t border-[#26262C] text-xs text-[#6B6E76]">
            High pairwise correlation reduces effective diversification, increasing aggregate tail risk.
          </div>
        </div>
      </div>
    </div>
  );
}

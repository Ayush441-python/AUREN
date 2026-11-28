"use client";

import { useState } from "react";
import { formatNumber } from "@/lib/format";
import {
  cellAppearance,
  highThreshold as CHART_HIGH_THRESHOLD,
} from "./heatmapCells";
import { cn } from "@/lib/cn";
import type { CorrelationMatrix } from "@/lib/types";

interface HeatmapProps {
  matrix: CorrelationMatrix;
}

interface Selection {
  row: string;
  column: string;
  value: number;
  high: boolean;
}

const highThreshold = CHART_HIGH_THRESHOLD;

export function Heatmap({ matrix }: HeatmapProps) {
  const columns = matrix.columns;
  const [selected, setSelected] = useState<Selection | null>(() => {
    if (!columns.length) return null;
    const value = matrix.data[0]?.[1] ?? 0;
    return {
      row: columns[0],
      column: columns[1] ?? columns[0],
      value,
      high: value > highThreshold,
    };
  });

  if (!columns.length) {
    return (
      <p className="border border-line bg-obsidian/60 px-4 py-3 text-xs text-muted">
        No correlation matrix was supplied for this portfolio.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="auren-scrollbar-none overflow-x-auto">
        <table className="w-full min-w-[560px] border-collapse text-center">
          <caption className="sr-only">
            Pairwise Pearson correlation coefficients for portfolio assets
          </caption>
          <thead>
            <tr>
              <th
                scope="col"
                className="border-b border-line px-2 py-2 text-left font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint"
              >
                Asset
              </th>
              {columns.map((column) => (
                <th
                  key={column}
                  scope="col"
                  className="border-b border-line px-1 py-2 font-mono text-[0.6rem] uppercase tracking-[0.1em] text-muted"
                  title={column}
                >
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {columns.map((row, rowIndex) => (
              <tr key={row}>
                <th
                  scope="row"
                  className="border-b border-line/60 px-2 py-1.5 text-left font-mono text-[0.62rem] uppercase tracking-[0.1em] text-muted"
                  title={row}
                >
                  {row}
                </th>
                {columns.map((column, columnIndex) => {
                  const value = matrix.data[rowIndex]?.[columnIndex] ?? 0;
                  const diagonal = rowIndex === columnIndex;
                  const high = !diagonal && value > highThreshold;
                  const active = selected?.row === row && selected.column === column;
                  return (
                    <td key={`${row}-${column}`} className="border-b border-line/40 p-1">
                      <button
                        type="button"
                        onFocus={() =>
                          setSelected({ row, column, value, high })
                        }
                        onMouseEnter={() =>
                          setSelected({ row, column, value, high })
                        }
                        onClick={() => setSelected({ row, column, value, high })}
                        aria-label={`${row} and ${column}, Pearson correlation ${formatNumber(
                          value,
                          2
                        )}${high ? ", above 0.70 high co-movement threshold" : ""}${
                          diagonal ? ", same asset" : ""
                        }`}
                        className={cn(
                          "w-full min-w-[48px] border px-1 py-2 font-mono text-[0.68rem] tabular transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-champagne",
                          active && "ring-1 ring-champagne/70",
                          high && "font-semibold"
                        )}
                        style={cellAppearance(value, diagonal)}
                      >
                        {formatNumber(value, 2)}
                      </button>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div
        aria-live="polite"
        className="flex flex-wrap items-center justify-between gap-3 border border-line bg-obsidian/60 px-4 py-3"
      >
        <div>
          <p className="font-mono text-[0.58rem] uppercase tracking-[0.18em] text-faint">
            Selected pair
          </p>
          <p className="mt-1 text-xs text-primary">
            {selected ? `${selected.row} × ${selected.column}` : "—"}
            <span className="ml-2 font-mono text-champagne tabular">
              r = {selected ? formatNumber(selected.value, 2) : "—"}
            </span>
          </p>
        </div>
        <p
          className={cn(
            "font-mono text-[0.62rem] uppercase tracking-[0.14em]",
            selected?.high ? "text-negative" : "text-muted"
          )}
        >
          {selected?.high ? "High co-movement, r > 0.70" : "Below high co-movement threshold"}
        </p>
      </div>

      <ul className="flex flex-wrap gap-x-5 gap-y-2 text-[0.62rem] text-muted">
        <li className="inline-flex items-center gap-2">
          <span aria-hidden="true" className="h-3 w-3 border border-positive/30 bg-positive/10" />
          Low or negative, ≤ 0.20
        </li>
        <li className="inline-flex items-center gap-2">
          <span aria-hidden="true" className="h-3 w-3 border border-line bg-elevated" />
          Moderate, 0.21–0.49
        </li>
        <li className="inline-flex items-center gap-2">
          <span aria-hidden="true" className="h-3 w-3 border border-gold/35 bg-gold/15" />
          Elevated, 0.50–0.70
        </li>
        <li className="inline-flex items-center gap-2">
          <span aria-hidden="true" className="h-3 w-3 border border-negative/45 bg-negative/25" />
          High, &gt; 0.70
        </li>
      </ul>
    </div>
  );
}

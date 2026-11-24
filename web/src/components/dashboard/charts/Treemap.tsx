"use client";

import { useMemo, useState } from "react";
import { EmptyState } from "@/components/ui/States";
import { formatPercent } from "@/lib/format";
import { cn } from "@/lib/cn";

interface TreemapProps {
  weights: Record<string, number>;
}

interface Tile {
  ticker: string;
  weight: number;
  x: number;
  y: number;
  width: number;
  height: number;
}

const width = 1000;
const height = 560;
const palette = ["#D4AF37", "#A39D90", "#7FA8A0", "#C49BC8", "#D48A6A", "#8FA6D4"];

function layoutWeights(entries: [string, number][], x: number, y: number, w: number, h: number): Tile[] {
  if (entries.length === 0) return [];
  if (entries.length === 1) {
    return [{ ticker: entries[0][0], weight: entries[0][1], x, y, width: w, height: h }];
  }

  const total = entries.reduce((sum, [, value]) => sum + value, 0);
  let split = 1;
  let bestDistance = Math.abs(entries[0][1] - total / 2);
  let running = entries[0][1];
  for (let index = 1; index < entries.length - 1; index += 1) {
    running += entries[index][1];
    const distance = Math.abs(running - total / 2);
    if (distance < bestDistance) {
      bestDistance = distance;
      split = index + 1;
    }
  }

  const first = entries.slice(0, split);
  const second = entries.slice(split);
  const firstTotal = first.reduce((sum, [, value]) => sum + value, 0);
  const ratio = total > 0 ? firstTotal / total : 0.5;

  if (w >= h) {
    const firstWidth = w * ratio;
    return [
      ...layoutWeights(first, x, y, firstWidth, h),
      ...layoutWeights(second, x + firstWidth, y, w - firstWidth, h),
    ];
  }

  const firstHeight = h * ratio;
  return [
    ...layoutWeights(first, x, y, w, firstHeight),
    ...layoutWeights(second, x, y + firstHeight, w, h - firstHeight),
  ];
}

export function Treemap({ weights }: TreemapProps) {
  const entries = useMemo(
    () =>
      Object.entries(weights)
        .filter(([, value]) => Number.isFinite(value) && value > 0)
        .sort((a, b) => b[1] - a[1]),
    [weights]
  );
  const tiles = useMemo(
    () => (entries.length ? layoutWeights(entries, 0, 0, width, height) : []),
    [entries]
  );
  const [activeTicker, setActiveTicker] = useState<string | null>(null);

  const active = tiles.find((tile) => tile.ticker === activeTicker) ?? tiles[0];

  if (!tiles.length) {
    return (
      <EmptyState
        title="No allocation data"
        description="The analysis response did not include positive asset weights to map."
      />
    );
  }

  return (
    <div className="space-y-4">
      <div
        className="relative aspect-[16/9] w-full min-w-0 overflow-hidden border border-line bg-obsidian"
        role="group"
        aria-label="Asset allocation treemap"
      >
        {tiles.map((tile, index) => {
          const color = palette[index % palette.length];
          const overThreshold = tile.weight > 0.3;
          return (
            <button
              key={tile.ticker}
              type="button"
              onClick={() => setActiveTicker(tile.ticker)}
              onFocus={() => setActiveTicker(tile.ticker)}
              onMouseEnter={() => setActiveTicker(tile.ticker)}
              aria-describedby="treemap-detail"
              aria-label={`${tile.ticker}, ${formatPercent(tile.weight)} of portfolio${
                overThreshold ? ", above 30 percent single-asset threshold" : ""
              }`}
              className={cn(
                "absolute inset-[2px] flex flex-col items-start justify-between overflow-hidden border p-2 text-left transition-colors duration-200 focus-visible:z-10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-champagne sm:p-3",
                overThreshold ? "border-negative/60" : "border-line/70"
              )}
              style={{
                left: `${(tile.x / width) * 100}%`,
                top: `${(tile.y / height) * 100}%`,
                width: `${(tile.width / width) * 100}%`,
                height: `${(tile.height / height) * 100}%`,
                backgroundColor: `${color}18`,
                boxShadow: `inset 0 0 0 1px ${color}22`,
              }}
            >
              <span className="flex max-w-full items-center gap-1.5">
                <span
                  aria-hidden="true"
                  className="h-2 w-2 shrink-0"
                  style={{ backgroundColor: color }}
                />
                <span className="truncate font-mono text-[0.6rem] uppercase tracking-[0.14em] text-primary sm:text-xs">
                  {tile.ticker}
                </span>
              </span>
              <span className="tabular font-mono text-sm text-highlight sm:text-xl">
                {formatPercent(tile.weight)}
              </span>
            </button>
          );
        })}
      </div>

      <div
        id="treemap-detail"
        aria-live="polite"
        className="flex flex-wrap items-center justify-between gap-3 border border-line bg-obsidian/60 px-4 py-3"
      >
        <div className="min-w-0">
          <p className="font-mono text-[0.58rem] uppercase tracking-[0.18em] text-faint">
            Selected position
          </p>
          <p className="mt-1 text-sm text-primary">
            {active?.ticker ?? "—"}
            <span className="ml-2 font-mono text-champagne tabular">
              {formatPercent(active?.weight ?? null)}
            </span>
          </p>
        </div>
        <p
          className={cn(
            "font-mono text-[0.62rem] uppercase tracking-[0.14em]",
            active && active.weight > 0.3 ? "text-negative" : "text-positive"
          )}
        >
          {active && active.weight > 0.3
            ? "Above 30% rule (+20 pts)"
            : "Within single-asset rule"}
        </p>
      </div>
    </div>
  );
}

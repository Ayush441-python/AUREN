"use client";

import { Layers3, PieChart, ScanLine } from "lucide-react";
import { formatNumber, formatPercent } from "@/lib/format";
import { cn } from "@/lib/cn";
import type { RiskAnalysis } from "@/lib/types";
import { Metric, Panel, PanelHeader } from "@/components/ui/Panel";
import { Treemap } from "@/components/dashboard/charts/Treemap";

interface ExposureViewProps {
  data: RiskAnalysis;
}

export function ExposureView({ data }: ExposureViewProps) {
  const holdings = Object.entries(data.normalized_weights).sort((a, b) => b[1] - a[1]);
  const sectors = Object.entries(data.sector_exposure).sort((a, b) => b[1] - a[1]);
  const { concentration } = data;

  return (
    <div className="space-y-7">
      <header className="border-b border-line pb-6">
        <p className="auren-eyebrow">Portfolio intelligence / Exposure</p>
        <h1 className="mt-3 font-display text-4xl leading-none text-primary sm:text-5xl">
          Capital exposure
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted">
          Asset and sector decomposition of the current weight vector. Every percentage below is
          derived from the supplied normalized weights or the grouped sector exposures in the
          analysis response.
        </p>
      </header>

      <section aria-label="Concentration metrics" className="grid grid-cols-1 gap-px border border-line bg-line sm:grid-cols-2 xl:grid-cols-4">
        <div className="bg-secondary px-5 py-5">
          <Metric
            label="Top asset"
            value={concentration.top_asset}
            detail={`${formatPercent(concentration.top_weight)} · above 30% adds +20 pts`}
            tone={concentration.top_weight > 0.3 ? "negative" : "gold"}
          />
        </div>
        <div className="bg-secondary px-5 py-5">
          <Metric
            label="Top three"
            value={formatPercent(concentration.top3_weight)}
            detail="Combined weight of the three largest positions"
          />
        </div>
        <div className="bg-secondary px-5 py-5">
          <Metric
            label="Effective assets"
            value={formatNumber(concentration.effective_assets, 2)}
            detail="1 / HHI · below 4 adds +15 pts"
            tone={concentration.effective_assets < 4 ? "negative" : "positive"}
          />
        </div>
        <div className="bg-secondary px-5 py-5">
          <Metric
            label="HHI"
            value={formatNumber(concentration.hhi, 4)}
            detail="Σ (wᵢ)², computed from normalized weights"
          />
        </div>
      </section>

      <Panel>
        <PanelHeader
          eyebrow="Weight topology"
          title="Asset allocation map"
          action={
            <span className="font-mono text-[0.6rem] uppercase tracking-[0.16em] text-faint">
              {holdings.length} positions
            </span>
          }
        />
        <div className="p-5 sm:p-6">
          <Treemap weights={data.normalized_weights} />
        </div>
      </Panel>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-12">
        <Panel className="xl:col-span-7">
          <PanelHeader
            eyebrow="Position ledger"
            title="Individual weights"
            action={
              <Layers3 aria-hidden="true" className="h-4 w-4 text-gold" />
            }
          />
          <div className="divide-y divide-line/60">
            {holdings.map(([ticker, weight], index) => (
              <div key={ticker} className="grid grid-cols-[2rem_minmax(0,1fr)_auto] items-center gap-3 px-5 py-4 sm:px-6">
                <span className="font-mono text-[0.62rem] text-faint tabular">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div className="min-w-0">
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="truncate font-mono text-xs uppercase tracking-[0.12em] text-primary">
                      {ticker}
                    </span>
                    <span className="sr-only">{formatPercent(weight)}</span>
                  </div>
                  <div
                    className="mt-2 h-1.5 w-full bg-elevated"
                    role="meter"
                    aria-label={`${ticker} weight`}
                    aria-valuenow={Math.round(weight * 100)}
                    aria-valuemin={0}
                    aria-valuemax={100}
                  >
                    <div
                      className={cn("h-full", weight > 0.3 ? "bg-negative/70" : "bg-champagne/70")}
                      style={{ width: `${Math.min(100, weight * 100)}%` }}
                    />
                  </div>
                </div>
                <span
                  className={cn(
                    "font-mono text-xs tabular",
                    weight > 0.3 ? "text-negative" : "text-highlight"
                  )}
                >
                  {formatPercent(weight)}
                </span>
              </div>
            ))}
          </div>
          <p className="border-t border-line px-5 py-3 font-mono text-[0.62rem] leading-relaxed text-faint sm:px-6">
            Bar lengths are proportional to allocation. Positions above 30% are marked because they
            trigger the single-asset concentration penalty.
          </p>
        </Panel>

        <Panel className="xl:col-span-5">
          <PanelHeader
            eyebrow="Group decomposition"
            title="Sector exposure"
            action={
              <PieChart aria-hidden="true" className="h-4 w-4 text-positive" />
            }
          />
          <div className="space-y-5 p-5 sm:p-6">
            {sectors.length ? (
              sectors.map(([sector, exposure]) => (
                <div key={sector}>
                  <div className="flex items-center justify-between gap-3">
                    <span className="truncate text-xs text-primary" title={sector}>
                      {sector}
                    </span>
                    <span
                      className={cn(
                        "font-mono text-xs tabular",
                        exposure > 0.5 ? "text-negative" : "text-muted"
                      )}
                    >
                      {formatPercent(exposure)}
                    </span>
                  </div>
                  <div
                    className="mt-2 h-1 w-full bg-elevated"
                    role="meter"
                    aria-label={`${sector} exposure`}
                    aria-valuenow={Math.round(exposure * 100)}
                    aria-valuemin={0}
                    aria-valuemax={100}
                  >
                    <div
                      className={cn("h-full", exposure > 0.5 ? "bg-negative/70" : "bg-positive/60")}
                      style={{ width: `${Math.min(100, exposure * 100)}%` }}
                    />
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs text-muted">No sector exposure was supplied.</p>
            )}
          </div>
          <div className="flex items-start gap-2 border-t border-line px-5 py-4 text-xs leading-relaxed text-faint sm:px-6">
            <ScanLine aria-hidden="true" className="mt-0.5 h-3.5 w-3.5 shrink-0 text-gold" />
            <span>
              A sector weight above 50% adds +15 points to the deterministic risk score.
            </span>
          </div>
        </Panel>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <Panel>
          <div className="p-5">
            <p className="auren-eyebrow">Concentration read</p>
            <p className="mt-3 font-display text-3xl text-primary tabular">
              {formatPercent(concentration.top3_weight)}
            </p>
            <p className="mt-2 text-xs leading-relaxed text-muted">
              Held in the three largest positions. This is a measured value, not a scored penalty
              rule.
            </p>
          </div>
        </Panel>
        <Panel>
          <div className="p-5">
            <p className="auren-eyebrow">Effective breadth</p>
            <p className="mt-3 font-display text-3xl text-primary tabular">
              {formatNumber(concentration.effective_assets, 2)}
            </p>
            <p className="mt-2 text-xs leading-relaxed text-muted">
              The HHI-weighted equivalent number of equally sized holdings.
            </p>
          </div>
        </Panel>
        <Panel>
          <div className="p-5">
            <p className="auren-eyebrow">Largest sector</p>
            <p className="mt-3 truncate font-display text-3xl text-primary" title={sectors[0]?.[0]}>
              {sectors[0]?.[0] ?? "—"}
            </p>
            <p className="mt-2 font-mono text-xs text-champagne tabular">
              {formatPercent(sectors[0]?.[1] ?? null)}
            </p>
          </div>
        </Panel>
      </div>
    </div>
  );
}

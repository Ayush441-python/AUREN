"use client";

import { Layers3, PieChart } from "lucide-react";
import { formatBoundaryPercent, formatNumber, formatPercent } from "@/lib/format";
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
    <div className="space-y-6">
      <div className="rounded-xl border border-line bg-secondary p-5">
        <h1 className="font-sans text-xl font-bold tracking-tight text-primary sm:text-2xl">
          Asset &amp; Sector Exposure
        </h1>
        <p className="mt-1 text-xs text-muted">
          Normalized portfolio weights, single-issuer limits, and sector concentration breakdown.
        </p>
      </div>

      {/* Concentration KPIs */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-xl border border-line bg-secondary p-4">
          <Metric
            label="Top Asset Weight"
            value={formatBoundaryPercent(concentration.top_weight, concentration.exceeds_30pct ?? concentration.top_weight > 0.3)}
            detail={`${concentration.top_asset} · >30% adds penalty`}
            tone={(concentration.exceeds_30pct ?? concentration.top_weight > 0.3) ? "negative" : "gold"}
          />
        </div>
        <div className="rounded-xl border border-line bg-secondary p-4">
          <Metric
            label="Top 3 Positions"
            value={formatPercent(concentration.top3_weight)}
            detail="Combined weight of 3 largest assets"
          />
        </div>
        <div className="rounded-xl border border-line bg-secondary p-4">
          <Metric
            label="Effective Bets (Neff)"
            value={formatNumber(concentration.effective_assets, 1)}
            detail="1 / HHI · below 4 adds penalty"
            tone={concentration.effective_assets < 4 ? "negative" : "positive"}
          />
        </div>
        <div className="rounded-xl border border-line bg-secondary p-4">
          <Metric
            label="HHI Index"
            value={formatNumber(concentration.hhi, 3)}
            detail="Σ (w_i)² across normalized portfolio"
          />
        </div>
      </div>

      {/* Treemap */}
      <Panel>
        <PanelHeader
          eyebrow="ALLOCATION TOPOLOGY"
          title="Relative Position Weights"
          action={
            <span className="font-mono text-xs text-muted">
              {holdings.length} assets held
            </span>
          }
        />
        <div className="p-5">
          <Treemap weights={data.normalized_weights} />
        </div>
      </Panel>

      {/* Tables: Holdings & Sector */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <Panel className="lg:col-span-7">
          <PanelHeader
            eyebrow="POSITION LEDGER"
            title="Individual Asset Breakdown"
            action={<Layers3 className="h-4 w-4 text-gold" />}
          />
          <div className="divide-y divide-line">
            {holdings.map(([ticker, weight], index) => (
              <div key={ticker} className="flex items-center justify-between gap-4 px-5 py-3 text-xs">
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <span className="font-mono text-[0.68rem] text-muted w-5">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-mono font-semibold uppercase text-primary">
                        {ticker}
                      </span>
                      <span className={cn(
                        "font-mono font-semibold",
                        weight > 0.3 ? "text-negative" : "text-primary"
                      )}>
                        {formatPercent(weight)}
                      </span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-elevated overflow-hidden">
                      <div
                        className={cn("h-full rounded-full", weight > 0.3 ? "bg-negative" : "bg-gold")}
                        style={{ width: `${Math.min(100, weight * 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="border-t border-line px-5 py-3 text-[0.68rem] text-muted">
            Positions exceeding 30% are highlighted and trigger single-asset concentration penalties.
          </div>
        </Panel>

        <Panel className="lg:col-span-5">
          <PanelHeader
            eyebrow="SECTOR AGGREGATION"
            title="Sector Exposure"
            action={<PieChart className="h-4 w-4 text-gold" />}
          />
          <div className="p-5 space-y-4">
            {sectors.length ? (
              sectors.map(([sector, exposure]) => (
                <div key={sector}>
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="text-primary font-medium">{sector}</span>
                    <span className={cn(
                      "font-mono font-semibold",
                      exposure > 0.5 ? "text-negative" : "text-muted"
                    )}>
                      {formatPercent(exposure)}
                    </span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-elevated overflow-hidden">
                    <div
                      className={cn("h-full rounded-full", exposure > 0.5 ? "bg-negative" : "bg-gold/80")}
                      style={{ width: `${Math.min(100, exposure * 100)}%` }}
                    />
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs text-muted">No sector classification available.</p>
            )}
          </div>
        </Panel>
      </div>
    </div>
  );
}

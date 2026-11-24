"use client";

import { useState } from "react";
import {
  ArrowUpRight,
  Calculator,
  ShieldAlert,
  TrendingDown,
} from "lucide-react";
import { formatNumber, formatPercent, formatSignedPercent } from "@/lib/format";
import { cn } from "@/lib/cn";
import type { RiskAnalysis } from "@/lib/types";
import type { DataStatus, DashboardTab } from "@/components/dashboard/Workstation";
import { Button } from "@/components/ui/Button";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { Panel, PanelHeader } from "@/components/ui/Panel";
import { NumbersUsedDrawer } from "@/components/drawer/NumbersUsedDrawer";
import { HistoricalCharts } from "@/components/dashboard/charts/HistoricalCharts";
import { RiskGauge } from "@/components/dashboard/charts/RiskGauge";
import { Treemap } from "@/components/dashboard/charts/Treemap";

interface OverviewViewProps {
  data: RiskAnalysis;
  status?: DataStatus;
  error?: string | null;
  portfolioName?: string;
  onNavigateTab?: (tab: DashboardTab) => void;
}

export function OverviewView({
  data,
  status = "reference",
  error = null,
  portfolioName = "Portfolio analysis",
  onNavigateTab,
}: OverviewViewProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const rankedHits = [...data.hits].sort((a, b) => b[0] - a[0]);
  const worstStress = Object.entries(data.stress).sort((a, b) => a[1] - b[1])[0];
  const worstDrawdown = Math.min(...(data.drawdown_series.length ? data.drawdown_series : [0]));

  return (
    <div className="space-y-7">
      <header className="flex flex-col gap-5 border-b border-line pb-6 xl:flex-row xl:items-end xl:justify-between">
        <div className="min-w-0">
          <p className="auren-eyebrow">Portfolio intelligence / Overview</p>
          <h1 className="mt-3 font-display text-4xl leading-none text-primary sm:text-5xl">
            Risk overview
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted">
            Deterministic analysis of <span className="text-primary">{portfolioName}</span> across
            concentration, volatility, co-movement, drawdown, and hypothetical shock responses.
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <RiskBadge level={data.level} score={data.score} />
            <span className="font-mono text-[0.6rem] uppercase tracking-[0.16em] text-faint">
              {status === "live"
                ? "Live engine result"
                : status === "stale"
                  ? "Previous analysis retained"
                  : "Bundled reference analysis"}
            </span>
          </div>
        </div>
        <Button variant="secondary" onClick={() => setDrawerOpen(true)} className="shrink-0">
          <Calculator aria-hidden="true" className="h-3.5 w-3.5 text-gold" />
          Audit numbers & formulas
        </Button>
      </header>

      {status === "stale" && error && (
        <div className="border border-negative/30 bg-negative/5 px-4 py-3 text-xs leading-relaxed text-primary">
          <span className="font-mono uppercase tracking-[0.16em] text-negative">Data notice: </span>
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-12">
        <Panel className="xl:col-span-5">
          <PanelHeader
            eyebrow="Composite measure"
            title="Risk score"
            action={
              <span className="font-mono text-[0.6rem] uppercase tracking-[0.16em] text-faint">
                0 – 100
              </span>
            }
          />
          <div className="p-5 sm:p-6">
            <RiskGauge score={data.score} level={data.level} />
            <p className="mt-4 text-xs leading-relaxed text-muted">
              Six deterministic penalty rules are applied to measured portfolio inputs. The tier
              boundaries are fixed: 0–34 Low, 35–64 Medium, and 65–100 High.
            </p>
            <div className="mt-5 grid grid-cols-2 gap-px border border-line bg-line">
              <div className="bg-secondary px-4 py-4">
                <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">
                  Effective assets
                </p>
                <p className="mt-2 font-mono text-xl text-primary tabular">
                  {formatNumber(data.concentration.effective_assets, 2)}
                </p>
                <p className="mt-1 font-mono text-[0.58rem] text-muted">1 / HHI</p>
              </div>
              <div className="bg-secondary px-4 py-4">
                <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">
                  HHI concentration
                </p>
                <p className="mt-2 font-mono text-xl text-primary tabular">
                  {formatNumber(data.concentration.hhi, 4)}
                </p>
                <p className="mt-1 font-mono text-[0.58rem] text-muted">Σ (wᵢ)²</p>
              </div>
            </div>
          </div>
        </Panel>

        <Panel className="xl:col-span-7">
          <PanelHeader
            eyebrow="Scored penalties"
            title="Primary risk drivers"
            action={
              <span className="font-mono text-[0.6rem] uppercase tracking-[0.16em] text-faint">
                {rankedHits.length} hits
              </span>
            }
          />
          <div className="p-5 sm:p-6">
            {rankedHits.length ? (
              <ol className="space-y-3">
                {rankedHits.map(([points, label], index) => (
                  <li
                    key={`${label}-${index}`}
                    className="flex items-start gap-3 border border-line/70 bg-obsidian/40 px-3 py-3"
                  >
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center border border-gold/30 bg-gold/10 font-mono text-[0.62rem] text-gold">
                      {index + 1}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block text-xs leading-relaxed text-primary">{label}</span>
                    </span>
                    <span className="shrink-0 font-mono text-xs text-champagne tabular">
                      +{points} pts
                    </span>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="border border-line bg-obsidian/40 px-4 py-3 text-xs text-muted">
                No scored penalties were returned in this analysis.
              </p>
            )}

            {data.reasons.length > 0 && (
              <div className="mt-5 border-t border-line pt-4">
                <p className="auren-eyebrow">Model notes</p>
                <ul className="mt-3 space-y-2">
                  {data.reasons.map((reason, index) => (
                    <li key={index} className="flex gap-2 text-xs leading-relaxed text-muted">
                      <span aria-hidden="true" className="mt-1.5 h-1 w-1 shrink-0 bg-gold" />
                      {reason}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Panel>
      </div>

      <section aria-labelledby="overview-kpis">
        <h2 id="overview-kpis" className="auren-eyebrow mb-3">
          Measured inputs
        </h2>
        <div className="grid grid-cols-1 gap-px border border-line bg-line sm:grid-cols-2 xl:grid-cols-4">
          <KpiCard
            label="Annualized volatility"
            value={formatPercent(data.volatility)}
            detail="σdaily × √252 · above 30% adds +20 pts"
            tone={data.volatility > 0.3 ? "negative" : "default"}
          />
          <KpiCard
            label="Max drawdown"
            value={formatSignedPercent(data.max_drawdown)}
            detail="Peak-to-trough · below −30% adds +15 pts"
            tone={data.max_drawdown < -0.3 ? "negative" : "default"}
          />
          <KpiCard
            label="Top asset"
            value={formatPercent(data.concentration.top_weight)}
            detail={`${data.concentration.top_asset} · above 30% adds +20 pts`}
            tone={data.concentration.top_weight > 0.3 ? "negative" : "default"}
          />
          <KpiCard
            label="Worst 21-session return"
            value={formatSignedPercent(data.worst_historical_periods.worst_month)}
            detail={`Worst day ${formatSignedPercent(data.worst_historical_periods.worst_day)}`}
          />
        </div>
      </section>

      <Panel>
        <PanelHeader
          eyebrow="Return history"
          title="Historical performance & drawdown"
          action={
            <span className="font-mono text-[0.6rem] uppercase tracking-[0.16em] text-faint">
              {data.dates.length} dates supplied
            </span>
          }
        />
        <div className="p-5 sm:p-6">
          <HistoricalCharts analysis={data} />
        </div>
      </Panel>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-12">
        <Panel className="xl:col-span-7">
          <PanelHeader
            eyebrow="Capital map"
            title="Asset allocation"
            action={
              <button
                type="button"
                onClick={() => onNavigateTab?.("exposure")}
                className="inline-flex items-center gap-1.5 font-mono text-[0.6rem] uppercase tracking-[0.14em] text-champagne hover:text-highlight"
              >
                Full exposure
                <ArrowUpRight aria-hidden="true" className="h-3 w-3" />
              </button>
            }
          />
          <div className="p-5 sm:p-6">
            <Treemap weights={data.normalized_weights} />
          </div>
        </Panel>

        <div className="space-y-5 xl:col-span-5">
          <Panel>
            <PanelHeader eyebrow="Underwater detail" title="Drawdown insight" />
            <div className="grid grid-cols-2 gap-px bg-line">
              <div className="bg-secondary px-4 py-4">
                <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">
                  Deepest trough in series
                </p>
                <p className="mt-2 font-mono text-lg text-negative tabular">
                  {formatPercent(worstDrawdown)}
                </p>
              </div>
              <div className="bg-secondary px-4 py-4">
                <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">
                  Historic maximum
                </p>
                <p className="mt-2 font-mono text-lg text-primary tabular">
                  {formatPercent(data.max_drawdown)}
                </p>
              </div>
            </div>
            <p className="px-4 py-3 text-xs leading-relaxed text-muted">
              Worst month is the lowest rolling 21 trading-session return, not a 30-calendar-day
              figure.
            </p>
          </Panel>

          {worstStress && (
            <Panel>
              <div className="p-5">
                <div className="flex items-start gap-3">
                  <span className="border border-negative/30 bg-negative/10 p-2 text-negative">
                    <TrendingDown aria-hidden="true" className="h-4 w-4" />
                  </span>
                  <div className="min-w-0">
                    <p className="auren-eyebrow">Most severe modeled shock</p>
                    <p className="mt-2 text-sm text-primary">{worstStress[0]}</p>
                    <p className="mt-1 font-mono text-xl text-negative tabular">
                      {formatPercent(worstStress[1])}
                    </p>
                    <p className="mt-2 text-xs leading-relaxed text-muted">
                      Hypothetical response under current weights, not an actual historical replay.
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => onNavigateTab?.("stress")}
                  className="mt-4 inline-flex items-center gap-2 border border-line px-3 py-2 font-mono text-[0.6rem] uppercase tracking-[0.14em] text-champagne transition-colors hover:border-gold/50 hover:text-highlight"
                >
                  Open stress sandbox
                  <ArrowUpRight aria-hidden="true" className="h-3 w-3" />
                </button>
              </div>
            </Panel>
          )}
        </div>
      </div>

      <p className="flex items-start gap-2 border-l-2 border-gold/50 pl-3 text-xs leading-relaxed text-faint">
        <ShieldAlert aria-hidden="true" className="mt-0.5 h-3.5 w-3.5 shrink-0 text-gold" />
        {data.disclaimer}
      </p>

      <NumbersUsedDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        data={data}
      />
    </div>
  );
}

function KpiCard({
  label,
  value,
  detail,
  tone = "default",
}: {
  label: string;
  value: string;
  detail: string;
  tone?: "default" | "negative";
}) {
  return (
    <div className="bg-secondary px-4 py-4">
      <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">{label}</p>
      <p
        className={cn(
          "mt-2 font-mono text-2xl tabular",
          tone === "negative" ? "text-negative" : "text-primary"
        )}
      >
        {value}
      </p>
      <p className="mt-2 text-[0.68rem] leading-relaxed text-muted">{detail}</p>
    </div>
  );
}

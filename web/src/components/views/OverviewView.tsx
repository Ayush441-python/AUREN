"use client";

import { useState } from "react";
import {
  ArrowUpRight,
  Calculator,
  RefreshCw,
  Share2,
  ShieldAlert,
  TrendingDown,
  BarChart3,
  Layers,
  Activity,
  Zap,
} from "lucide-react";
import { formatNumber, formatPercent, formatSignedPercent } from "@/lib/format";
import { cn } from "@/lib/cn";
import type { RiskAnalysis } from "@/lib/types";
import type { DataStatus, DashboardTab } from "@/components/dashboard/Workstation";
import { Button } from "@/components/ui/Button";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { Panel, PanelHeader } from "@/components/ui/Panel";
import { NumbersUsedDrawer } from "@/components/drawer/NumbersUsedDrawer";
import { O1RebalanceModal } from "@/components/modals/O1RebalanceModal";
import { OnchainAttestModal } from "@/components/modals/OnchainAttestModal";
import { ShareScorecardModal } from "@/components/modals/ShareScorecardModal";
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
  const [shareOpen, setShareOpen] = useState(false);
  const [attestOpen, setAttestOpen] = useState(false);
  const [o1Open, setO1Open] = useState(false);
  const rankedHits = [...data.hits].sort((a, b) => b[0] - a[0]);
  const worstStress = Object.entries(data.stress).sort((a, b) => a[1] - b[1])[0];
  const worstDrawdown = Math.min(...(data.drawdown_series.length ? data.drawdown_series : [0]));

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex flex-col gap-4 rounded-xl border border-line bg-secondary p-4 sm:p-5 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2.5 sm:gap-3">
            <h1 className="font-sans text-xl font-bold tracking-tight text-primary sm:text-2xl">
              {portfolioName}
            </h1>
            <RiskBadge level={data.level} score={data.score} />
          </div>
          <p className="mt-1 text-xs text-muted">
            Institutional portfolio risk decomposition · {data.dates.length} sessions analyzed
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 shrink-0">
          <Button variant="primary" size="sm" onClick={() => setAttestOpen(true)}>
            <Zap aria-hidden="true" className="h-3.5 w-3.5 mr-1 shrink-0" />
            <span>Attest On-Chain (Base)</span>
          </Button>
          <Button variant="secondary" size="sm" onClick={() => setO1Open(true)}>
            <RefreshCw aria-hidden="true" className="h-3.5 w-3.5 text-gold mr-1 shrink-0" />
            <span>o1 Rebalance</span>
          </Button>
          <Button variant="secondary" size="sm" onClick={() => setShareOpen(true)}>
            <Share2 aria-hidden="true" className="h-3.5 w-3.5 text-gold mr-1 shrink-0" />
            <span>Share to X</span>
          </Button>
          <Button variant="secondary" size="sm" onClick={() => setDrawerOpen(true)}>
            <Calculator aria-hidden="true" className="h-3.5 w-3.5 text-gold mr-1 shrink-0" />
            <span>Formula &amp; Audit Trail</span>
          </Button>
        </div>
      </div>

      {/* Engine or Empty Wallet Notice */}
      {error && (
        <div className={cn(
          "rounded-lg border px-4 py-3 text-xs leading-relaxed flex items-center justify-between gap-3",
          error.includes("add stocks")
            ? "border-gold/40 bg-gold/10 text-highlight"
            : "border-negative/40 bg-negative/10 text-negative"
        )}>
          <div>
            <span className="font-semibold uppercase tracking-wider font-mono">
              {error.includes("add stocks") ? "Notice: " : "Engine Notice: "}
            </span>
            <span>{error}</span>
          </div>
          {error.includes("add stocks") && onNavigateTab && (
            <button
              onClick={() => onNavigateTab("portfolio" as any)}
              className="shrink-0 text-xs font-semibold text-gold underline underline-offset-2 hover:text-white"
            >
              Custom Portfolio
            </button>
          )}
        </div>
      )}

      {/* KPI Stats Strip */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-xl border border-line bg-secondary p-4">
          <div className="flex items-center justify-between text-muted">
            <span className="font-mono text-[0.68rem] uppercase tracking-wider">Ann. Volatility</span>
            <Activity className="h-3.5 w-3.5 text-gold" />
          </div>
          <p className={cn(
            "mt-2 font-mono text-2xl font-bold tabular-nums",
            data.volatility > 0.3 ? "text-negative" : "text-primary"
          )}>
            {formatPercent(data.volatility)}
          </p>
          <span className="mt-1 block text-[0.68rem] text-muted">σdaily × √252</span>
        </div>

        <div className="rounded-xl border border-line bg-secondary p-4">
          <div className="flex items-center justify-between text-muted">
            <span className="font-mono text-[0.68rem] uppercase tracking-wider">Max Drawdown</span>
            <TrendingDown className="h-3.5 w-3.5 text-negative" />
          </div>
          <p className={cn(
            "mt-2 font-mono text-2xl font-bold tabular-nums",
            data.max_drawdown < -0.3 ? "text-negative" : "text-primary"
          )}>
            {formatSignedPercent(data.max_drawdown)}
          </p>
          <span className="mt-1 block text-[0.68rem] text-muted">Peak-to-trough decline</span>
        </div>

        <div className="rounded-xl border border-line bg-secondary p-4">
          <div className="flex items-center justify-between text-muted">
            <span className="font-mono text-[0.68rem] uppercase tracking-wider">Top Asset Exposure</span>
            <BarChart3 className="h-3.5 w-3.5 text-gold" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-mono text-2xl font-bold tabular-nums text-primary">
              {formatPercent(data.concentration.top_weight)}
            </span>
            <span className="font-mono text-xs font-semibold text-gold">
              {data.concentration.top_asset}
            </span>
          </div>
          <span className="mt-1 block text-[0.68rem] text-muted">Single-issuer weight</span>
        </div>

        <div className="rounded-xl border border-line bg-secondary p-4">
          <div className="flex items-center justify-between text-muted">
            <span className="font-mono text-[0.68rem] uppercase tracking-wider">Effective Assets (Neff)</span>
            <Layers className="h-3.5 w-3.5 text-positive" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-mono text-2xl font-bold tabular-nums text-primary">
              {formatNumber(data.concentration.effective_assets, 1)}
            </span>
            <span className="font-mono text-xs text-muted">bets</span>
          </div>
          <span className="mt-1 block text-[0.68rem] text-muted">
            HHI: {formatNumber(data.concentration.hhi, 3)}
          </span>
        </div>
      </div>

      {/* Main Analysis Split: Risk Gauge & Primary Drivers */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <Panel className="lg:col-span-5">
          <PanelHeader
            eyebrow="RISK SCORE METER"
            title="Composite Vulnerability"
            action={
              <span className="font-mono text-xs font-semibold text-gold">
                {Math.round(data.score)} / 100
              </span>
            }
          />
          <div className="p-5">
            <RiskGauge score={data.score} level={data.level} />
            <div className="mt-4 rounded-lg border border-line bg-elevated p-3 text-xs text-muted">
              <span className="font-semibold text-primary">Fixed Methodology Tiers:</span> 0–34 Low Risk, 35–64 Medium Risk, and 65–100 High Risk. Derived from concentration, correlation, volatility, and stress test impacts.
            </div>
          </div>
        </Panel>

        <Panel className="lg:col-span-7">
          <PanelHeader
            eyebrow="AUDITED PENALTY TRIGGERS"
            title="Primary Risk Drivers"
            action={
              <span className="font-mono text-xs text-muted">
                {rankedHits.length} rules active
              </span>
            }
          />
          <div className="p-5">
            {rankedHits.length ? (
              <div className="space-y-2">
                {rankedHits.map(([points, label], index) => (
                  <div
                    key={`${label}-${index}`}
                    className="flex items-center justify-between rounded-lg border border-line bg-elevated px-3 py-2.5 text-xs"
                  >
                    <div className="flex items-center gap-2.5 min-w-0 pr-3">
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded border border-line bg-secondary font-mono text-[0.65rem] font-bold text-gold">
                        {index + 1}
                      </span>
                      <span className="truncate text-primary">{label}</span>
                    </div>
                    <span className="shrink-0 font-mono font-semibold text-gold tabular-nums">
                      +{points} pts
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-lg border border-positive/30 bg-positive/10 p-4 text-xs text-positive">
                Optimal diversification achieved. No risk penalty thresholds triggered.
              </div>
            )}

            {data.reasons.length > 0 && (
              <div className="mt-4 border-t border-line pt-3">
                <span className="font-mono text-[0.65rem] font-semibold uppercase tracking-wider text-muted">
                  Engine Observations
                </span>
                <ul className="mt-2 space-y-1.5 text-xs text-muted">
                  {data.reasons.map((reason, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-gold" />
                      <span>{reason}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Panel>
      </div>

      {/* Historical Performance & Drawdown Charts */}
      <Panel>
        <PanelHeader
          eyebrow="TIMESERIES ANALYSIS"
          title="Portfolio Performance & Cumulative Drawdown"
          action={
            <span className="font-mono text-xs text-muted">
              {data.dates.length} trading days
            </span>
          }
        />
        <div className="p-5">
          <HistoricalCharts analysis={data} />
        </div>
      </Panel>

      {/* Allocation Treemap & Stress Insight */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <Panel className="lg:col-span-7">
          <PanelHeader
            eyebrow="CAPITAL WEIGHTS"
            title="Normalized Asset Allocation"
            action={
              <button
                type="button"
                onClick={() => onNavigateTab?.("asset-allocation")}
                className="flex items-center gap-1 font-mono text-xs font-semibold text-gold transition-colors hover:text-highlight"
              >
                <span>Exposure View</span>
                <ArrowUpRight className="h-3 w-3" />
              </button>
            }
          />
          <div className="p-5">
            <Treemap weights={data.normalized_weights} />
          </div>
        </Panel>

        <div className="space-y-6 lg:col-span-5">
          <Panel>
            <PanelHeader eyebrow="DRAWDOWN PROFILE" title="Tail Risk Metrics" />
            <div className="grid grid-cols-2 divide-x divide-line border-b border-line">
              <div className="p-4">
                <span className="font-mono text-[0.65rem] uppercase tracking-wider text-muted">
                  Worst 21-Day Period
                </span>
                <p className="mt-1.5 font-mono text-lg font-bold text-negative tabular-nums">
                  {formatSignedPercent(data.worst_historical_periods.worst_month)}
                </p>
              </div>
              <div className="p-4">
                <span className="font-mono text-[0.65rem] uppercase tracking-wider text-muted">
                  Worst Single Session
                </span>
                <p className="mt-1.5 font-mono text-lg font-bold text-negative tabular-nums">
                  {formatSignedPercent(data.worst_historical_periods.worst_day)}
                </p>
              </div>
            </div>
            <div className="p-4 text-xs text-muted">
              Trough: <span className="font-mono text-negative">{formatPercent(worstDrawdown)}</span> below running peak.
            </div>
          </Panel>

          {worstStress && (
            <Panel>
              <div className="p-5">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[0.65rem] font-semibold uppercase tracking-wider text-gold">
                    Macro Shock Sensitivity
                  </span>
                  <button
                    type="button"
                    onClick={() => onNavigateTab?.("stress-testing")}
                    className="flex items-center gap-1 font-mono text-xs text-gold hover:text-highlight"
                  >
                    <span>Run Shocks</span>
                    <ArrowUpRight className="h-3 w-3" />
                  </button>
                </div>
                <div className="mt-3 flex items-center justify-between rounded-lg border border-line bg-elevated p-3">
                  <div>
                    <p className="text-xs font-semibold text-primary">{worstStress[0]}</p>
                    <p className="text-[0.68rem] text-muted">Estimated scenario portfolio decline</p>
                  </div>
                  <span className="font-mono text-lg font-bold text-negative tabular-nums">
                    {formatPercent(worstStress[1])}
                  </span>
                </div>
              </div>
            </Panel>
          )}
        </div>
      </div>

      {/* Institutional Disclaimer */}
      <div className="flex items-start gap-2.5 rounded-lg border border-line bg-secondary px-4 py-3 text-xs text-muted">
        <ShieldAlert className="h-4 w-4 shrink-0 text-gold mt-0.5" />
        <p className="leading-relaxed">{data.disclaimer}</p>
      </div>

      <NumbersUsedDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        data={data}
      />
      <ShareScorecardModal
        isOpen={shareOpen}
        onClose={() => setShareOpen(false)}
        data={data}
        portfolioName={portfolioName}
      />
      <OnchainAttestModal
        isOpen={attestOpen}
        onClose={() => setAttestOpen(false)}
        data={data}
        portfolioName={portfolioName}
      />
      <O1RebalanceModal
        isOpen={o1Open}
        onClose={() => setO1Open(false)}
        data={data}
        portfolioName={portfolioName}
      />
    </div>
  );
}

"use client";

import { useMemo, useState } from "react";
import { Activity, AlertCircle, ArrowRight, RotateCcw, SlidersHorizontal } from "lucide-react";
import { formatNumber, formatPercent, formatSignedPercent } from "@/lib/format";
import { cn } from "@/lib/cn";
import type { RiskAnalysis } from "@/lib/types";
import type { SimulationComparison } from "@/components/dashboard/Workstation";
import { Button } from "@/components/ui/Button";
import { Panel, PanelHeader } from "@/components/ui/Panel";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { ScenarioBars } from "@/components/dashboard/charts/ScenarioBars";

interface StressViewProps {
  data: RiskAnalysis;
  onSimulate?: (newWeights: Record<string, number>) => void;
  isSimulating?: boolean;
  simulation?: SimulationComparison | null;
  error?: string | null;
}

function normalize(weights: Record<string, number>): Record<string, number> {
  const positive = Object.entries(weights).filter(([, value]) => Number.isFinite(value) && value > 0);
  const total = positive.reduce((sum, [, value]) => sum + value, 0);
  if (!total) return {};
  return Object.fromEntries(positive.map(([ticker, value]) => [ticker, value / total]));
}

export function StressView({
  data,
  onSimulate,
  isSimulating = false,
  simulation = null,
  error = null,
}: StressViewProps) {
  const [sandbox, setSandbox] = useState<{
    source: RiskAnalysis;
    weights: Record<string, number>;
  } | null>(null);

  const weights = sandbox?.source === data ? sandbox.weights : data.normalized_weights;

  const total = useMemo(
    () => Object.values(weights).reduce((sum, value) => sum + value, 0),
    [weights]
  );
  const normalizedTotal = Math.abs(total - 1) < 0.005;
  const worstScenario = Object.entries(data.stress).sort((a, b) => a[1] - b[1])[0];

  const setSandboxWeights = (next: (current: Record<string, number>) => Record<string, number>) => {
    setSandbox({ source: data, weights: next(weights) });
  };

  const updateWeight = (ticker: string, percent: number) => {
    setSandboxWeights((current) => ({ ...current, [ticker]: percent / 100 }));
  };

  const reset = () => setSandbox({ source: data, weights: { ...data.normalized_weights } });

  const runSimulation = () => {
    if (!onSimulate || !normalizedTotal || isSimulating) return;
    onSimulate(normalize(weights));
  };

  const comparison = simulation;
  const baseline = comparison?.baseline ?? data;
  const result = comparison?.result ?? null;

  return (
    <div className="space-y-7">
      <header className="flex flex-col gap-5 border-b border-line pb-6 xl:flex-row xl:items-end xl:justify-between">
        <div className="min-w-0">
          <p className="auren-eyebrow">Portfolio intelligence / Stress</p>
          <h1 className="mt-3 font-display text-4xl leading-none text-primary sm:text-5xl">
            Stress & scenarios
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted">
            Hypothetical shock responses under the current weight vector. These scenarios are model
            inputs applied to the portfolio, not replays of historical market events.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <RiskBadge level={data.level} score={data.score} />
          {worstScenario && (
            <span className="border border-negative/30 bg-negative/5 px-2.5 py-1 font-mono text-[0.62rem] uppercase tracking-[0.14em] text-negative">
              Worst model: {worstScenario[0]} {formatPercent(worstScenario[1])}
            </span>
          )}
        </div>
      </header>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-12">
        <Panel className="xl:col-span-7">
          <PanelHeader
            eyebrow="Shock response"
            title="Scenario impacts"
            action={<Activity aria-hidden="true" className="h-4 w-4 text-gold" />}
          />
          <div className="p-5 sm:p-6">
            <ScenarioBars stress={data.stress} />
          </div>
        </Panel>

        <Panel className="xl:col-span-5">
          <PanelHeader eyebrow="Model definition" title="How to read this" />
          <div className="space-y-4 p-5 sm:p-6 text-xs leading-relaxed text-muted">
            <p>
              Each bar applies a deterministic percentage shock to the assets in the current
              portfolio and aggregates the result using the same normalized weights shown in the
              sandbox.
            </p>
            <p>
              The scenarios are intentionally hypothetical. They test sensitivity; they do not
              forecast returns or reproduce a specific historical crisis.
            </p>
            {worstScenario && (
              <div className="border-l-2 border-negative/60 pl-4">
                <p className="auren-eyebrow">Most severe input</p>
                <p className="mt-2 text-primary">{worstScenario[0]}</p>
                <p className="mt-1 font-mono text-xl text-negative tabular">
                  {formatPercent(worstScenario[1])}
                </p>
              </div>
            )}
          </div>
        </Panel>
      </div>

      <Panel>
        <PanelHeader
          eyebrow="Live recalculation"
          title="What-if sandbox"
          action={
            <div className="flex items-center gap-3">
              <span
                aria-live="polite"
                className={cn(
                  "font-mono text-[0.62rem] uppercase tracking-[0.14em] tabular",
                  normalizedTotal ? "text-positive" : "text-champagne"
                )}
              >
                Total {formatPercent(total)}
              </span>
              <Button variant="ghost" onClick={reset} disabled={isSimulating} className="px-3 py-1.5">
                <RotateCcw aria-hidden="true" className="h-3 w-3" />
                Reset
              </Button>
            </div>
          }
        />
        <div className="p-5 sm:p-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {Object.entries(weights).map(([ticker, weight]) => {
              const percent = Math.round(weight * 100);
              return (
                <div key={ticker} className="border border-line bg-obsidian/50 px-4 py-4">
                  <div className="flex items-center justify-between gap-3">
                    <label
                      htmlFor={`stress-${ticker}`}
                      className="font-mono text-xs uppercase tracking-[0.14em] text-primary"
                    >
                      {ticker}
                    </label>
                    <span className="font-mono text-xs text-champagne tabular">{percent}%</span>
                  </div>
                  <input
                    id={`stress-${ticker}`}
                    type="range"
                    min={0}
                    max={100}
                    step={1}
                    value={percent}
                    onChange={(event) => updateWeight(ticker, Number(event.target.value))}
                    disabled={isSimulating}
                    className="mt-4 w-full accent-[#D4AF37]"
                  />
                </div>
              );
            })}
          </div>

          {error && (
            <div role="alert" className="mt-5 flex items-start gap-2 border border-negative/30 bg-negative/5 px-4 py-3 text-xs leading-relaxed text-primary">
              <AlertCircle aria-hidden="true" className="mt-0.5 h-3.5 w-3.5 shrink-0 text-negative" />
              {error}
            </div>
          )}

          <div className="mt-6 flex flex-col gap-3 border-t border-line pt-5 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs leading-relaxed text-muted">
              {onSimulate
                ? normalizedTotal
                  ? "Weights sum to 100%. Recalculation calls the risk engine and replaces the displayed analysis."
                  : "Adjust weights until the total is 100% before recalculating."
                : "Simulation controls are read-only in this embedded view."}
            </p>
            {onSimulate && (
              <Button
                variant="primary"
                onClick={runSimulation}
                disabled={!normalizedTotal || isSimulating}
              >
                <SlidersHorizontal aria-hidden="true" className="h-3.5 w-3.5" />
                {isSimulating ? "Recalculating..." : "Recalculate risk"}
                <ArrowRight aria-hidden="true" className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
        </div>
      </Panel>

      {comparison && result && (
        <Panel>
          <PanelHeader
            eyebrow="Before / after"
            title="Simulation comparison"
            action={
              <span className="font-mono text-[0.6rem] uppercase tracking-[0.14em] text-faint">
                Engine recalculated
              </span>
            }
          />
          <div className="p-5 sm:p-6">
            <div className="grid grid-cols-1 gap-px border border-line bg-line sm:grid-cols-2 xl:grid-cols-4">
              <div className="bg-secondary px-4 py-4">
                <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">Score</p>
                <p className="mt-2 font-mono text-xl text-primary tabular">
                  {formatNumber(baseline.score, 0)}
                  <span className="mx-2 text-faint">→</span>
                  <span className="text-champagne">{formatNumber(result.score, 0)}</span>
                </p>
              </div>
              <div className="bg-secondary px-4 py-4">
                <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">Risk level</p>
                <p className="mt-2 text-sm text-primary">
                  {baseline.level}
                  <span className="mx-2 text-faint">→</span>
                  <span className="text-champagne">{result.level}</span>
                </p>
              </div>
              <div className="bg-secondary px-4 py-4">
                <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">Volatility</p>
                <p className="mt-2 font-mono text-sm tabular">
                  {formatPercent(baseline.volatility)}
                  <span className="mx-2 text-faint">→</span>
                  <span className="text-champagne">{formatPercent(result.volatility)}</span>
                </p>
              </div>
              <div className="bg-secondary px-4 py-4">
                <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">Max drawdown</p>
                <p className="mt-2 font-mono text-sm tabular">
                  {formatSignedPercent(baseline.max_drawdown)}
                  <span className="mx-2 text-faint">→</span>
                  <span className="text-champagne">{formatSignedPercent(result.max_drawdown)}</span>
                </p>
              </div>
            </div>

            <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-2">
              <div>
                <p className="auren-eyebrow mb-3">Baseline scenarios</p>
                <ScenarioBars stress={baseline.stress} />
              </div>
              <div>
                <p className="auren-eyebrow mb-3">Recalculated scenarios</p>
                <ScenarioBars stress={result.stress} />
              </div>
            </div>

            <div className="mt-5 flex flex-wrap gap-2">
              {Object.entries(comparison.weights).map(([ticker, weight]) => (
                <span
                  key={ticker}
                  className="border border-line bg-secondary px-2 py-1 font-mono text-[0.62rem] text-muted"
                >
                  {ticker} {formatPercent(weight)}
                </span>
              ))}
            </div>
          </div>
        </Panel>
      )}

      <p className="border-l-2 border-gold/50 pl-3 text-xs leading-relaxed text-faint">
        {data.disclaimer}
      </p>
    </div>
  );
}

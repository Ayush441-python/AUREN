"use client";

import { useMemo, useState } from "react";
import { Activity, RotateCcw } from "lucide-react";
import { formatPercent } from "@/lib/format";
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
    <div className="space-y-6">
      <div className="flex flex-col gap-4 rounded-xl border border-line bg-secondary p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-sans text-xl font-bold tracking-tight text-primary sm:text-2xl">
            Stress Testing &amp; What-If Simulation
          </h1>
          <p className="mt-1 text-xs text-muted">
            Hypothetical scenario stress testing and real-time portfolio reweighting sandbox.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <RiskBadge level={data.level} score={data.score} />
          {worstScenario && (
            <span className="rounded border border-negative/30 bg-negative/10 px-2.5 py-1 font-mono text-xs font-semibold text-negative">
              Worst Shock: {worstScenario[0]} ({formatPercent(worstScenario[1])})
            </span>
          )}
        </div>
      </div>

      {/* Scenario Bars and Explanation */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <Panel className="lg:col-span-7">
          <PanelHeader
            eyebrow="SCENARIO SHOCK IMPACT"
            title="Macro Crisis Simulation"
            action={<Activity className="h-4 w-4 text-gold" />}
          />
          <div className="p-5">
            <ScenarioBars stress={data.stress} />
          </div>
        </Panel>

        <Panel className="lg:col-span-5">
          <PanelHeader eyebrow="METHODOLOGY" title="Deterministic Shocks" />
          <div className="p-5 space-y-4 text-xs text-muted leading-relaxed">
            <p>
              Each scenario represents a predetermined market factor shock applied directly across current portfolio weights.
            </p>
            {worstScenario && (
              <div className="rounded-lg border border-negative/30 bg-negative/5 p-4">
                <span className="font-mono text-[0.65rem] font-semibold uppercase tracking-wider text-negative">
                  Maximum Modeled Loss
                </span>
                <p className="mt-1 text-sm font-semibold text-primary">{worstScenario[0]}</p>
                <p className="mt-1 font-mono text-2xl font-bold text-negative">
                  {formatPercent(worstScenario[1])}
                </p>
              </div>
            )}
            <p className="text-[0.68rem]">
              Simulations test structural portfolio vulnerabilities and correlation breakdowns rather than forecasting price paths.
            </p>
          </div>
        </Panel>
      </div>

      {/* What-If Sandbox */}
      <Panel>
        <PanelHeader
          eyebrow="WHAT-IF REWEIGHTING"
          title="Interactive Weight Sandbox"
          action={
            <div className="flex items-center gap-3">
              <span
                className={cn(
                  "font-mono text-xs font-semibold",
                  normalizedTotal ? "text-positive" : "text-gold"
                )}
              >
                Sum: {formatPercent(total)}
              </span>
              <Button variant="ghost" onClick={reset} disabled={isSimulating} className="h-8 px-2.5 text-xs">
                <RotateCcw className="h-3 w-3 mr-1" />
                Reset
              </Button>
            </div>
          }
        />
        <div className="p-5">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(weights).map(([ticker, weight]) => {
              const percent = Math.round(weight * 100);
              return (
                <div key={ticker} className="rounded-lg border border-line bg-elevated p-3.5">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs font-bold uppercase text-primary">
                      {ticker}
                    </span>
                    <span className="font-mono text-xs font-semibold text-gold">
                      {percent}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={percent}
                    onChange={(e) => updateWeight(ticker, Number(e.target.value))}
                    disabled={isSimulating}
                    className="w-full accent-gold h-1.5 bg-[#272B30] rounded-lg cursor-pointer"
                  />
                </div>
              );
            })}
          </div>

          <div className="mt-6 flex flex-wrap items-center justify-between gap-4 border-t border-line pt-4">
            <span className="text-xs text-muted">
              Adjust weights to recalculate risk scores, factor concentrations, and shock scenarios.
            </span>
            <Button
              onClick={runSimulation}
              disabled={!normalizedTotal || isSimulating}
              className="px-5 py-2 font-semibold text-xs"
            >
              {isSimulating ? "Recalculating..." : "Execute Recalculation"}
            </Button>
          </div>

          {/* Simulation Comparison if Available */}
          {result && (
            <div className="mt-6 rounded-lg border border-line bg-secondary p-4">
              <span className="font-mono text-xs font-semibold uppercase tracking-wider text-gold">
                Sandbox Recalculation Result
              </span>
              <div className="mt-3 grid grid-cols-3 gap-4">
                <div>
                  <span className="text-xs text-muted">Risk Score</span>
                  <div className="mt-1 flex items-baseline gap-2">
                    <span className="font-mono text-xl font-bold text-primary">{Math.round(result.score)}</span>
                    <span className="font-mono text-xs text-muted">vs {Math.round(baseline.score)}</span>
                  </div>
                </div>
                <div>
                  <span className="text-xs text-muted">Volatility</span>
                  <div className="mt-1">
                    <span className="font-mono text-xl font-bold text-primary">{formatPercent(result.volatility)}</span>
                  </div>
                </div>
                <div>
                  <span className="text-xs text-muted">Effective Assets</span>
                  <div className="mt-1">
                    <span className="font-mono text-xl font-bold text-primary">{result.concentration.effective_assets.toFixed(1)}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </Panel>
    </div>
  );
}

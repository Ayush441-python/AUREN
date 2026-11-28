"use client";

import { Link2 } from "lucide-react";
import { formatNumber } from "@/lib/format";
import type { RiskAnalysis } from "@/lib/types";
import { Metric, Panel, PanelHeader } from "@/components/ui/Panel";
import { Heatmap } from "@/components/dashboard/charts/Heatmap";

interface CorrelationViewProps {
  data: RiskAnalysis;
}

export function CorrelationView({ data }: CorrelationViewProps) {
  const pairs = data.correlated_pairs;
  const scored = pairs.length >= 2;

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-line bg-secondary p-5">
        <h1 className="font-sans text-xl font-bold tracking-tight text-primary sm:text-2xl">
          Pairwise Correlation Matrix
        </h1>
        <p className="mt-1 text-xs text-muted">
          Pearson correlation coefficients derived from aligned daily simple returns to diagnose diversification health.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-xl border border-line bg-secondary p-4">
          <Metric
            label="Matrix Constituents"
            value={data.correlation_matrix.columns.length}
            detail="Aligned assets in return series"
          />
        </div>
        <div className="rounded-xl border border-line bg-secondary p-4">
          <Metric
            label="Highly Correlated Pairs (>0.70)"
            value={pairs.length}
            detail="Coupled pairs that elevate vulnerability"
            tone={pairs.length ? "negative" : "positive"}
          />
        </div>
        <div className="rounded-xl border border-line bg-secondary p-4">
          <Metric
            label="Correlation Rule Penalty"
            value={scored ? "+15 pts" : "+0 pts"}
            detail="≥2 pairs >0.70 adds 15 risk points"
            tone={scored ? "negative" : "positive"}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <Panel className="lg:col-span-8">
          <PanelHeader
            eyebrow="HEATMAP DECOMPOSITION"
            title="Pearson Correlation Grid"
            action={
              <span className="font-mono text-xs text-muted">
                {data.correlation_matrix.columns.length} × {data.correlation_matrix.columns.length}
              </span>
            }
          />
          <div className="p-5 overflow-x-auto">
            <Heatmap matrix={data.correlation_matrix} />
          </div>
        </Panel>

        <Panel className="lg:col-span-4">
          <PanelHeader
            eyebrow="RISK COUPLES"
            title="Pairs with r > 0.70"
            action={<Link2 className="h-4 w-4 text-gold" />}
          />
          <div className="p-5">
            {pairs.length ? (
              <div className="space-y-2.5">
                {pairs.map(([assetA, assetB, corr]) => (
                  <div
                    key={`${assetA}-${assetB}`}
                    className="flex items-center justify-between rounded-lg border border-line bg-elevated px-3 py-2.5 text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-semibold text-primary">{assetA}</span>
                      <span className="text-muted">↔</span>
                      <span className="font-mono font-semibold text-primary">{assetB}</span>
                    </div>
                    <span className="font-mono font-bold text-negative">
                      {formatNumber(corr, 2)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-lg border border-positive/30 bg-positive/10 p-4 text-xs text-positive">
                No asset pairs exhibit severe historical correlation above 0.70.
              </div>
            )}

            <div className="mt-4 rounded-lg border border-line bg-elevated p-3 text-xs text-muted">
              High pairwise correlation indicates assets move synchronously during downturns, reducing true portfolio diversification.
            </div>
          </div>
        </Panel>
      </div>
    </div>
  );
}

"use client";

import { Grid2X2, Link2, ShieldCheck } from "lucide-react";
import { formatNumber } from "@/lib/format";
import { cn } from "@/lib/cn";
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
    <div className="space-y-7">
      <header className="border-b border-line pb-6">
        <p className="auren-eyebrow">Portfolio intelligence / Co-movement</p>
        <h1 className="mt-3 font-display text-4xl leading-none text-primary sm:text-5xl">
          Correlation matrix
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted">
          Pairwise Pearson coefficients computed from aligned daily simple returns, not log
          returns. Coefficients describe historical co-movement; they do not imply causation.
        </p>
      </header>

      <section aria-label="Correlation summary" className="grid grid-cols-1 gap-px border border-line bg-line sm:grid-cols-3">
        <div className="bg-secondary px-5 py-5">
          <Metric
            label="Assets in matrix"
            value={data.correlation_matrix.columns.length}
            detail="Aligned price series with available return observations"
          />
        </div>
        <div className="bg-secondary px-5 py-5">
          <Metric
            label="Pairs above 0.70"
            value={pairs.length}
            detail="Off-diagonal pairs with Pearson r greater than 0.70"
            tone={pairs.length ? "negative" : "positive"}
          />
        </div>
        <div className="bg-secondary px-5 py-5">
          <Metric
            label="Scoring impact"
            value={scored ? "+15 pts" : "+0 pts"}
            detail="Two or more pairs above 0.70 add 15 points"
            tone={scored ? "negative" : "positive"}
          />
        </div>
      </section>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-12">
        <Panel className="xl:col-span-8">
          <PanelHeader
            eyebrow="Pairwise matrix"
            title="Pearson r"
            action={
              <Grid2X2 aria-hidden="true" className="h-4 w-4 text-gold" />
            }
          />
          <div className="p-5 sm:p-6">
            <Heatmap matrix={data.correlation_matrix} />
          </div>
        </Panel>

        <Panel className="xl:col-span-4">
          <PanelHeader
            eyebrow="Threshold watch"
            title="High co-movement pairs"
            action={
              <span className="font-mono text-[0.6rem] uppercase tracking-[0.16em] text-faint">
                {pairs.length} flagged
              </span>
            }
          />
          <div className="p-5 sm:p-6">
            {pairs.length ? (
              <ol className="space-y-3">
                {pairs.map(([assetA, assetB, value], index) => (
                  <li
                    key={`${assetA}-${assetB}-${index}`}
                    className="border border-negative/25 bg-negative/[0.04] px-4 py-3"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="min-w-0 truncate font-mono text-xs uppercase tracking-[0.12em] text-primary">
                        {assetA} <span className="text-faint">×</span> {assetB}
                      </span>
                      <span className="font-mono text-sm text-negative tabular">
                        {formatNumber(value, 2)}
                      </span>
                    </div>
                    <p className="mt-2 text-[0.68rem] leading-relaxed text-muted">
                      Above the 0.70 threshold. These assets have moved together closely over the
                      supplied return window.
                    </p>
                  </li>
                ))}
              </ol>
            ) : (
              <div className="border border-positive/25 bg-positive/[0.04] px-4 py-4">
                <p className="flex items-center gap-2 text-xs text-positive">
                  <ShieldCheck aria-hidden="true" className="h-4 w-4" />
                  No pair exceeds 0.70
                </p>
                <p className="mt-2 text-xs leading-relaxed text-muted">
                  The correlation penalty is not triggered for this weight vector.
                </p>
              </div>
            )}

            <div className="mt-5 border-t border-line pt-4">
              <p className="auren-eyebrow">Interpretation</p>
              <p className="mt-2 text-xs leading-relaxed text-muted">
                High pairwise correlation reduces the diversification benefit of holding multiple
                assets because positions are more likely to decline at the same time.
              </p>
            </div>
          </div>
        </Panel>
      </div>

      <Panel>
        <PanelHeader
          eyebrow="Methodology"
          title="How this matrix is built"
          action={<Link2 aria-hidden="true" className="h-4 w-4 text-gold" />}
        />
        <div className="grid grid-cols-1 gap-px bg-line md:grid-cols-3">
          <div className="bg-secondary px-5 py-5">
            <p className="font-mono text-[0.62rem] uppercase tracking-[0.16em] text-champagne">
              01 · Align
            </p>
            <p className="mt-2 text-xs leading-relaxed text-muted">
              Price series are aligned by date and limited to assets present in the current weight
              vector.
            </p>
          </div>
          <div className="bg-secondary px-5 py-5">
            <p className="font-mono text-[0.62rem] uppercase tracking-[0.16em] text-champagne">
              02 · Transform
            </p>
            <p className="mt-2 text-xs leading-relaxed text-muted">
              Simple daily returns are calculated as P<sub>t</sub> / P<sub>t−1</sub> − 1. Diagonal
              values equal 1.
            </p>
          </div>
          <div className="bg-secondary px-5 py-5">
            <p className="font-mono text-[0.62rem] uppercase tracking-[0.16em] text-champagne">
              03 · Score
            </p>
            <p className={cn("mt-2 text-xs leading-relaxed", scored ? "text-negative" : "text-muted")}>
              Two or more off-diagonal pairs with r &gt; 0.70 add 15 penalty points.
            </p>
          </div>
        </div>
      </Panel>
    </div>
  );
}

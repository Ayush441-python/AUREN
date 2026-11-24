"use client";

import { useMemo, useState } from "react";
import { AlertCircle, Calculator, CheckCircle2, FileText, Sparkles } from "lucide-react";
import { generateAIReport } from "@/lib/api";
import { formatNumber, formatPercent, formatSignedPercent } from "@/lib/format";
import { cn } from "@/lib/cn";
import type { AIReportResponse, RiskAnalysis } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { Panel, PanelHeader } from "@/components/ui/Panel";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { NumbersUsedDrawer } from "@/components/drawer/NumbersUsedDrawer";

interface ReportViewProps {
  data: RiskAnalysis;
}

export function ReportView({ data }: ReportViewProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [reportState, setReportState] = useState<{
    source: RiskAnalysis;
    report: AIReportResponse | null;
    error: string | null;
  } | null>(null);
  const [loading, setLoading] = useState(false);

  const currentState = reportState?.source === data ? reportState : null;
  const report = currentState?.report ?? null;
  const error = currentState?.error ?? null;

  const metrics = useMemo(
    () => ({
      score: data.score,
      level: data.level,
      normalized_weights: data.normalized_weights,
      reasons: data.reasons,
      hits: data.hits,
      correlation_matrix: data.correlation_matrix,
      concentration: data.concentration,
      volatility: data.volatility,
      max_drawdown: data.max_drawdown,
      sector_exposure: data.sector_exposure,
      correlated_pairs: data.correlated_pairs,
      stress: data.stress,
      worst_historical_periods: data.worst_historical_periods,
    }),
    [data]
  );

  const topSector = Object.entries(data.sector_exposure).sort((a, b) => b[1] - a[1])[0];

  const generate = async () => {
    setLoading(true);
    setReportState({ source: data, report: null, error: null });
    try {
      const result = await generateAIReport(metrics);
      setReportState({ source: data, report: result, error: null });
    } catch (generateError) {
      setReportState({
        source: data,
        report: null,
        error:
          generateError instanceof Error && generateError.message
            ? generateError.message
            : "The report service did not return a narrative.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-7">
      <header className="flex flex-col gap-5 border-b border-line pb-6 xl:flex-row xl:items-end xl:justify-between">
        <div className="min-w-0">
          <p className="auren-eyebrow">Portfolio intelligence / Report</p>
          <h1 className="mt-3 font-display text-4xl leading-none text-primary sm:text-5xl">
            Verified narrative
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted">
            A deterministic summary from the current analysis, paired with an optional AI narrative
            generated from the exact metrics shown here. Numbers are checked against the payload
            sent to the model.
          </p>
        </div>
        <Button variant="secondary" onClick={() => setDrawerOpen(true)} className="shrink-0">
          <Calculator aria-hidden="true" className="h-3.5 w-3.5 text-gold" />
          Audit numbers used
        </Button>
      </header>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-12">
        <div className="space-y-5 xl:col-span-8">
          <Panel>
            <PanelHeader
              eyebrow="Deterministic summary"
              title="Executive assessment"
              action={<RiskBadge level={data.level} score={data.score} />}
            />
            <div className="space-y-5 p-5 sm:p-6 text-sm leading-relaxed text-muted">
              <p>
                The portfolio scores{" "}
                <span className="font-mono text-champagne tabular">{formatNumber(data.score, 0)} / 100</span>
                , placing it in the <span className="text-primary">{data.level} risk</span> tier.
                The largest single position is{" "}
                <span className="font-mono text-primary">{data.concentration.top_asset}</span> at{" "}
                <span className="font-mono text-champagne tabular">
                  {formatPercent(data.concentration.top_weight)}
                </span>
                {topSector && (
                  <>
                    , and the largest sector group is{" "}
                    <span className="text-primary">{topSector[0]}</span> at{" "}
                    <span className="font-mono text-champagne tabular">
                      {formatPercent(topSector[1])}
                    </span>
                  </>
                )}
                .
              </p>

              <div className="grid grid-cols-1 gap-px border border-line bg-line sm:grid-cols-2">
                <div className="bg-secondary px-4 py-4">
                  <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">
                    Annualized volatility
                  </p>
                  <p className="mt-2 font-mono text-xl text-primary tabular">
                    {formatPercent(data.volatility)}
                  </p>
                  <p className="mt-1 text-[0.68rem] text-faint">Daily standard deviation × √252</p>
                </div>
                <div className="bg-secondary px-4 py-4">
                  <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">
                    Maximum drawdown
                  </p>
                  <p className="mt-2 font-mono text-xl text-negative tabular">
                    {formatSignedPercent(data.max_drawdown)}
                  </p>
                  <p className="mt-1 text-[0.68rem] text-faint">Peak-to-trough decline</p>
                </div>
                <div className="bg-secondary px-4 py-4">
                  <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">
                    Effective assets
                  </p>
                  <p className="mt-2 font-mono text-xl text-primary tabular">
                    {formatNumber(data.concentration.effective_assets, 2)}
                  </p>
                  <p className="mt-1 text-[0.68rem] text-faint">Inverse HHI</p>
                </div>
                <div className="bg-secondary px-4 py-4">
                  <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">
                    Pairs above 0.70
                  </p>
                  <p className="mt-2 font-mono text-xl text-primary tabular">
                    {data.correlated_pairs.length}
                  </p>
                  <p className="mt-1 text-[0.68rem] text-faint">Two or more add 15 points</p>
                </div>
              </div>

              <div>
                <p className="auren-eyebrow mb-3">Scored reasons</p>
                <ul className="space-y-2">
                  {data.reasons.length ? (
                    data.reasons.map((reason, index) => (
                      <li key={index} className="flex gap-2 text-xs text-muted">
                        <span aria-hidden="true" className="mt-1.5 h-1 w-1 shrink-0 bg-gold" />
                        {reason}
                      </li>
                    ))
                  ) : (
                    <li className="text-xs text-muted">No penalty rules were triggered.</li>
                  )}
                </ul>
              </div>
            </div>
          </Panel>

          <Panel>
            <PanelHeader
              eyebrow="Optional model output"
              title="AI narrative"
              action={
                <Button onClick={generate} disabled={loading} variant="primary">
                  <Sparkles aria-hidden="true" className="h-3.5 w-3.5" />
                  {loading ? "Generating..." : report ? "Regenerate" : "Generate report"}
                </Button>
              }
            />
            <div className="p-5 sm:p-6">
              {error && (
                <div role="alert" className="flex items-start gap-2 border border-negative/30 bg-negative/5 px-4 py-3 text-xs leading-relaxed text-primary">
                  <AlertCircle aria-hidden="true" className="mt-0.5 h-3.5 w-3.5 shrink-0 text-negative" />
                  {error}
                </div>
              )}

              {!report && !error && (
                <div className="flex min-h-40 flex-col items-center justify-center text-center">
                  <FileText aria-hidden="true" className="h-7 w-7 text-faint" />
                  <p className="mt-4 font-display text-2xl text-primary">No narrative generated</p>
                  <p className="mt-2 max-w-md text-xs leading-relaxed text-muted">
                    The model call is explicit. Nothing is generated until you request it, and the
                    exact metrics payload is displayed below.
                  </p>
                </div>
              )}

              {report && (
                <div className="space-y-5">
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-3">
                    <span className="font-mono text-[0.62rem] uppercase tracking-[0.16em] text-faint">
                      Model: {report.model}
                    </span>
                    <span
                      className={cn(
                        "inline-flex items-center gap-1.5 font-mono text-[0.62rem] uppercase tracking-[0.14em]",
                        report.unverified_numbers.length ? "text-negative" : "text-positive"
                      )}
                    >
                      {report.unverified_numbers.length ? (
                        <AlertCircle aria-hidden="true" className="h-3.5 w-3.5" />
                      ) : (
                        <CheckCircle2 aria-hidden="true" className="h-3.5 w-3.5" />
                      )}
                      {report.unverified_numbers.length
                        ? `${report.unverified_numbers.length} unverified number${
                            report.unverified_numbers.length === 1 ? "" : "s"
                          }`
                        : "No unverified numbers detected"}
                    </span>
                  </div>

                  {report.unverified_numbers.length > 0 && (
                    <div className="border border-negative/30 bg-negative/5 px-4 py-3 text-xs leading-relaxed text-primary">
                      <span className="font-mono uppercase tracking-[0.14em] text-negative">
                        Verification notice:{" "}
                      </span>
                      The response contains numbers not found in the metrics payload. Treat the
                      narrative with caution:{" "}
                      <span className="font-mono">
                        {report.unverified_numbers.join(", ")}
                      </span>
                    </div>
                  )}

                  <div className="whitespace-pre-wrap text-sm leading-[1.8] text-primary">
                    {report.report}
                  </div>

                  <p className="border-l-2 border-gold/50 pl-3 text-xs leading-relaxed text-faint">
                    {report.disclaimer}
                  </p>
                </div>
              )}
            </div>
          </Panel>
        </div>

        <div className="space-y-5 xl:col-span-4">
          <Panel>
            <PanelHeader eyebrow="Model input" title="Metrics sent" />
            <div className="p-4">
              <CodeBlock code={JSON.stringify(metrics, null, 2)} title="risk-metrics.json" />
            </div>
          </Panel>

          <Panel>
            <PanelHeader eyebrow="Verification" title="Number policy" />
            <div className="space-y-3 p-5 text-xs leading-relaxed text-muted">
              <p>
                The backend compares every number in the generated narrative with the numeric
                values in the metrics payload above.
              </p>
              <p>
                Small whole numbers and 100 are ignored by the checker. Verification status is
                reported from the API, not assumed by the interface.
              </p>
              <p className="text-faint">{data.disclaimer}</p>
            </div>
          </Panel>
        </div>
      </div>

      <NumbersUsedDrawer isOpen={drawerOpen} onClose={() => setDrawerOpen(false)} data={data} />
    </div>
  );
}

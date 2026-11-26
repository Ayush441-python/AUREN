"use client";

import { useEffect, useRef, useState } from "react";
import { Calculator, Check, Copy, ShieldCheck, X } from "lucide-react";
import { formatBoundaryPercent, formatNumber, formatPercent, formatSignedPercent } from "@/lib/format";
import { cn } from "@/lib/cn";
import type { RiskAnalysis } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { CodeBlock } from "@/components/ui/CodeBlock";

interface NumbersUsedDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  data: RiskAnalysis;
}

export function NumbersUsedDrawer({ isOpen, onClose, data }: NumbersUsedDrawerProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    const previous = document.activeElement as HTMLElement | null;
    const panel = panelRef.current;
    panel?.focus();

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
      if (event.key !== "Tab" || !panel) return;
      const focusable = panel.querySelectorAll<HTMLElement>(
        'button:not([disabled]), [href], input:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", onKeyDown);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = "";
      previous?.focus();
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const maxSector = Object.entries(data.sector_exposure).sort((a, b) => b[1] - a[1])[0];
  const payload = {
    score: data.score,
    level: data.level,
    normalized_weights: data.normalized_weights,
    reasons: data.reasons,
    hits: data.hits,
    observed_sessions: data.dates.length,
    concentration: data.concentration,
    annualized_volatility: data.volatility,
    max_historical_drawdown: data.max_drawdown,
    sector_exposure: data.sector_exposure,
    correlation_matrix: data.correlation_matrix,
    correlated_pairs: data.correlated_pairs,
    stress_scenarios: data.stress,
    worst_historical_periods: data.worst_historical_periods,
  };
  const rawJson = JSON.stringify(payload, null, 2);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(rawJson);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  };

  const rows = [
    {
      label: "Largest holding",
      value: data.concentration.top_asset,
      measured: formatBoundaryPercent(data.concentration.top_weight, data.concentration.exceeds_30pct ?? data.concentration.top_weight > 0.3),
      condition: "> 30%",
      points: 20,
      triggered: data.concentration.exceeds_30pct ?? data.concentration.top_weight > 0.3,
    },
    {
      label: "Effective assets",
      value: formatNumber(data.concentration.effective_assets, 2),
      measured: "1 / HHI",
      condition: "< 4",
      points: 15,
      triggered: data.concentration.effective_assets < 4,
    },
    {
      label: "Annualized volatility",
      value: formatPercent(data.volatility),
      measured: "σdaily × √252",
      condition: "> 30%",
      points: 20,
      triggered: data.volatility > 0.3,
    },
    {
      label: "Maximum drawdown",
      value: formatSignedPercent(data.max_drawdown),
      measured: "min(Pₜ / peak − 1)",
      condition: "< −30%",
      points: 15,
      triggered: data.max_drawdown < -0.3,
    },
    {
      label: "Pairs above threshold",
      value: String(data.correlated_pairs.length),
      measured: "Pearson r, simple returns",
      condition: "≥ 2 pairs, r > 0.70",
      points: 15,
      triggered: data.correlated_pairs.length >= 2,
    },
    {
      label: "Largest sector",
      value: maxSector?.[0] ?? "—",
      measured: maxSector ? formatPercent(maxSector[1]) : "—",
      condition: "> 50%",
      points: 15,
      triggered: (maxSector?.[1] ?? 0) > 0.5,
    },
  ];

  const triggeredPoints = rows.reduce((sum, row) => sum + (row.triggered ? row.points : 0), 0);

  return (
    <div className="fixed inset-0 z-[100] flex justify-end">
      <button
        type="button"
        aria-label="Close audit drawer"
        onClick={onClose}
        className="absolute inset-0 cursor-default bg-black/80 backdrop-blur-sm"
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="audit-drawer-title"
        tabIndex={-1}
        className="auren-panel relative flex h-full w-full max-w-2xl flex-col overflow-hidden outline-none"
      >
        <div className="flex items-start justify-between gap-4 border-b border-line px-6 py-5">
          <div className="flex items-start gap-3">
            <span className="border border-gold/30 bg-gold/10 p-2 text-champagne">
              <Calculator aria-hidden="true" className="h-4 w-4" />
            </span>
            <div>
              <p className="auren-eyebrow">Audit trail</p>
              <h2 id="audit-drawer-title" className="mt-2 font-display text-3xl leading-none text-primary">
                Numbers used
              </h2>
              <p className="mt-2 text-xs leading-relaxed text-muted">
                Exact inputs, thresholds, and rule contributions behind the current score.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close audit drawer"
            className="border border-line p-2 text-muted transition-colors hover:border-gold/50 hover:text-highlight"
          >
            <X aria-hidden="true" className="h-4 w-4" />
          </button>
        </div>

        <div className="auren-scrollbar-none min-h-0 flex-1 space-y-6 overflow-y-auto px-6 py-5">
          <div className="border border-positive/25 bg-positive/[0.04] px-4 py-4">
            <p className="flex items-center gap-2 font-mono text-[0.62rem] uppercase tracking-[0.16em] text-positive">
              <ShieldCheck aria-hidden="true" className="h-3.5 w-3.5" />
              Deterministic rule proof
            </p>
            <p className="mt-2 text-xs leading-relaxed text-muted">
              The rule total is {triggeredPoints} points. The analysis reports {data.score} points
              in the {data.level} tier. Tiers are 0–34 Low, 35–64 Medium, and 65–100 High.
            </p>
          </div>

          <div>
            <p className="auren-eyebrow mb-3">Scored inputs</p>
            <div className="auren-scrollbar-none overflow-x-auto border border-line">
              <table className="w-full min-w-[620px] text-left text-xs">
                <caption className="sr-only">Risk scoring rules and measured values</caption>
                <thead className="border-b border-line bg-secondary/70 text-faint">
                  <tr>
                    <th scope="col" className="px-3 py-3 font-mono text-[0.58rem] uppercase tracking-[0.14em]">Rule</th>
                    <th scope="col" className="px-3 py-3 font-mono text-[0.58rem] uppercase tracking-[0.14em]">Measured</th>
                    <th scope="col" className="px-3 py-3 font-mono text-[0.58rem] uppercase tracking-[0.14em]">Condition</th>
                    <th scope="col" className="px-3 py-3 font-mono text-[0.58rem] uppercase tracking-[0.14em]">Points</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line/60">
                  {rows.map((row) => (
                    <tr key={row.label} className={cn(row.triggered && "bg-negative/[0.03]")}>
                      <th scope="row" className="px-3 py-3 font-normal text-primary">
                        {row.label}
                      </th>
                      <td className="px-3 py-3 font-mono text-muted">
                        {row.value}
                        <span className="ml-2 text-faint">{row.measured}</span>
                      </td>
                      <td className="px-3 py-3 font-mono text-muted">{row.condition}</td>
                      <td
                        className={cn(
                          "px-3 py-3 font-mono tabular",
                          row.triggered ? "text-negative" : "text-faint"
                        )}
                      >
                        {row.triggered ? `+${row.points}` : "+0"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <p className="auren-eyebrow mb-3">Engine hits</p>
            {data.hits.length ? (
              <ol className="space-y-2">
                {data.hits.map(([points, reason], index) => (
                  <li key={`${reason}-${index}`} className="flex items-start justify-between gap-3 border border-line bg-obsidian/40 px-3 py-2.5 text-xs">
                    <span className="text-primary">{reason}</span>
                    <span className="shrink-0 font-mono text-champagne tabular">+{points}</span>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="border border-line bg-obsidian/40 px-3 py-3 text-xs text-muted">
                No rule conditions were triggered.
              </p>
            )}
          </div>

          <div>
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <p className="auren-eyebrow">Exact analysis payload</p>
              <Button variant="terminal" onClick={copy} className="px-3 py-1.5">
                {copied ? <Check aria-hidden="true" className="h-3 w-3" /> : <Copy aria-hidden="true" className="h-3 w-3" />}
                {copied ? "Copied" : "Copy JSON"}
              </Button>
            </div>
            <span aria-live="polite" className="sr-only">
              {copied ? "Audit payload copied" : ""}
            </span>
            <CodeBlock code={rawJson} title="analysis.json" />
          </div>

          <p className="border-l-2 border-gold/50 pl-3 text-xs leading-relaxed text-faint">
            {data.disclaimer}
          </p>
        </div>
      </div>
    </div>
  );
}

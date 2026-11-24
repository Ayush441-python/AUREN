import {
  Activity,
  FileText,
  Grid3X3,
  LayoutDashboard,
  PieChart,
  ShieldCheck,
} from "lucide-react";
import { ButtonLink } from "@/components/ui/Button";
import { Panel } from "@/components/ui/Panel";
import { Wordmark } from "@/components/ui/Wordmark";
import { cn } from "@/lib/cn";

const tabs = [
  { label: "Risk Overview", Icon: LayoutDashboard },
  { label: "Exposure & Factor", Icon: PieChart },
  { label: "Correlation Matrix", Icon: Grid3X3 },
  { label: "Stress & Sandbox", Icon: Activity },
  { label: "AI Verification", Icon: FileText },
  { label: "Proof & API", Icon: ShieldCheck },
];

const metrics = [
  "Risk score",
  "Annualized volatility",
  "Max drawdown",
  "Effective assets",
];

const stressRows = ["Historical scenario", "Custom scenario"];

export function ProductPreview() {
  return (
    <section
      id="preview"
      aria-labelledby="preview-heading"
      className="relative overflow-hidden border-b border-line/40 bg-secondary/30 py-24 sm:py-32"
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute left-1/2 top-1/3 h-[30rem] w-[60rem] -translate-x-1/2 rounded-full bg-gold/[0.04] blur-[130px]"
      />
      <div className="relative mx-auto max-w-[1400px] px-5 sm:px-8 lg:px-12">
        <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="auren-eyebrow">04 / The Workstation</p>
            <h2
              id="preview-heading"
              className="auren-display mt-6 text-[clamp(2.75rem,4.5vw,4.5rem)] text-primary"
            >
              One interface. Every layer.
            </h2>
          </div>
          <p className="max-w-md text-sm leading-relaxed text-muted">
            Interface preview — values populate from your portfolio.
          </p>
        </div>

        <div
          role="group"
          aria-label="AUREN dashboard interface preview"
          className="mt-12 overflow-hidden border border-line/70 bg-obsidian shadow-[0_50px_140px_-70px_rgba(212,175,55,0.35)]"
        >
          <div className="flex items-center justify-between gap-4 border-b border-line/70 bg-secondary/70 px-4 py-3 sm:px-6">
            <Wordmark compact />
            <span className="font-mono text-[0.55rem] uppercase tracking-[0.22em] text-faint">
              Workstation
            </span>
          </div>

          <div className="flex gap-2 overflow-x-auto border-b border-line/70 bg-secondary/50 p-3 sm:hidden">
            {tabs.map((tab) => (
              <span
                key={tab.label}
                className="shrink-0 border border-line/70 px-2.5 py-1.5 font-mono text-[0.55rem] uppercase tracking-[0.12em] text-faint"
              >
                {tab.label}
              </span>
            ))}
          </div>

          <div className="grid grid-cols-[3.25rem_minmax(0,1fr)] sm:grid-cols-[13rem_minmax(0,1fr)]">
            <aside className="hidden border-r border-line/70 bg-secondary/50 p-3 sm:block">
              <p className="auren-eyebrow px-2">Navigate</p>
              <ul className="mt-4 space-y-1">
                {tabs.map((tab, index) => {
                  const Icon = tab.Icon;
                  return (
                    <li key={tab.label}>
                      <div
                        className={cn(
                          "flex items-center gap-2 px-2 py-2 font-mono text-[0.58rem] uppercase leading-tight tracking-[0.1em] text-faint",
                          index === 0 && "border-l border-gold bg-elevated/60 text-champagne"
                        )}
                      >
                        <Icon aria-hidden="true" className="h-3.5 w-3.5 shrink-0" />
                        <span className="min-w-0">{tab.label}</span>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </aside>

            <div className="min-w-0">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line/70 px-4 py-4 sm:px-6">
                <div>
                  <p className="auren-eyebrow">Risk Overview</p>
                  <p className="mt-2 font-display text-2xl leading-none text-primary">
                    Portfolio analysis
                  </p>
                </div>
                <span className="border border-line px-3 py-1.5 font-mono text-[0.55rem] uppercase tracking-[0.16em] text-faint">
                  Connect a portfolio to populate
                </span>
              </div>

              <div className="grid gap-3 p-3 sm:grid-cols-2 sm:p-6 lg:grid-cols-4">
                {metrics.map((metric) => (
                  <Panel key={metric} className="p-4 sm:p-5">
                    <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">
                      {metric}
                    </p>
                    <p className="mt-4 font-display text-4xl leading-none text-faint">—</p>
                    <p className="mt-3 text-[0.65rem] text-faint">Awaiting analysis</p>
                  </Panel>
                ))}
              </div>

              <div className="grid gap-3 px-3 pb-3 sm:grid-cols-[1.4fr_1fr] sm:px-6 sm:pb-6">
                <Panel className="p-4 sm:p-5">
                  <p className="auren-eyebrow">Correlation Matrix</p>
                  <div className="mt-5 grid grid-cols-[3.25rem_repeat(4,minmax(0,1fr))] gap-px border border-line/50 bg-line/40">
                    {Array.from({ length: 25 }, (_, index) => (
                      <div
                        key={index}
                        className={cn(
                          "flex h-8 items-center justify-center bg-obsidian font-mono text-[0.6rem] text-faint",
                          index === 0 && "bg-elevated"
                        )}
                      >
                        {index === 0 ? "" : "—"}
                      </div>
                    ))}
                  </div>
                  <p className="mt-4 text-[0.65rem] text-faint">
                    Pairwise values appear after analysis.
                  </p>
                </Panel>

                <Panel className="p-4 sm:p-5">
                  <p className="auren-eyebrow">Stress &amp; Sandbox</p>
                  <ul className="mt-5 divide-y divide-line/50 border-y border-line/50">
                    {stressRows.map((row) => (
                      <li key={row} className="flex items-center justify-between gap-3 py-3">
                        <span className="text-[0.7rem] text-muted">{row}</span>
                        <span className="font-mono text-sm text-faint">—</span>
                      </li>
                    ))}
                  </ul>
                  <p className="mt-4 text-[0.65rem] text-faint">
                    Scenario results appear after analysis.
                  </p>
                </Panel>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-4 border-t border-line/70 bg-secondary/40 px-4 py-4 sm:px-6">
                <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">
                  Interface preview — values populate from your portfolio.
                </p>
                <ButtonLink href="/dashboard" variant="secondary" className="px-4 py-2">
                  Open the Workstation
                </ButtonLink>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

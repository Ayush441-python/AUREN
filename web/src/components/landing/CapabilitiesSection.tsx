import {
  ShieldAlert,
  Grid3X3,
  TrendingDown,
  FileCheck2,
  PieChart,
  Code2,
} from "lucide-react";

const capabilities = [
  {
    icon: ShieldAlert,
    title: "Portfolio Risk Assessment",
    description:
      "Composite risk scoring calibrated across concentration, return correlation, historical volatility, and tail-risk metrics.",
  },
  {
    icon: PieChart,
    title: "Asset & Factor Exposure",
    description:
      "Allocation breakdown across individual assets, sectors, and asset classes to pinpoint true capital concentration.",
  },
  {
    icon: Grid3X3,
    title: "Pairwise Correlation Matrix",
    description:
      "Pearson correlation derived on aligned daily returns to surface hidden co-movement that standard diversification misses.",
  },
  {
    icon: TrendingDown,
    title: "Macro Scenario Stress Testing",
    description:
      "Instantaneous simulation of historical macro shocks (GFC, 2020 Liquidity, Tech Selloff) on active portfolio weights.",
  },
  {
    icon: FileCheck2,
    title: "AI Synthesis & Verification",
    description:
      "LLM-generated portfolio risk reports with deterministic numerical verification to eliminate hallucinated metrics.",
  },
  {
    icon: Code2,
    title: "Institutional API Transparency",
    description:
      "Open, audited formulas and programmatic API access so quantitative teams can integrate metrics into internal pipelines.",
  },
];

export function CapabilitiesSection() {
  return (
    <section
      id="capabilities"
      aria-labelledby="capabilities-heading"
      className="border-b border-line bg-secondary py-16 sm:py-24"
    >
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8 lg:px-12">
        <div className="max-w-2xl">
          <span className="font-mono text-xs font-semibold uppercase tracking-wider text-gold">
            CORE CAPABILITIES
          </span>
          <h2
            id="capabilities-heading"
            className="mt-3 font-sans text-3xl font-bold tracking-tight text-primary sm:text-4xl"
          >
            Every dimension of risk, in one unified terminal.
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-muted sm:text-base">
            Six institutional modules built upon a single deterministic calculation engine.
          </p>
        </div>

        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {capabilities.map((cap) => {
            const Icon = cap.icon;
            return (
              <div
                key={cap.title}
                className="group rounded-xl border border-line bg-[#14171B] p-6 transition-colors hover:border-gold/40"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-line bg-secondary text-gold">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 font-sans text-base font-semibold text-primary">
                  {cap.title}
                </h3>
                <p className="mt-2 text-xs leading-relaxed text-muted">
                  {cap.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

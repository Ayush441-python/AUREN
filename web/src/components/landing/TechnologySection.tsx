import { cn } from "@/lib/cn";

const pipeline = [
  "Weights",
  "Aligned history",
  "Simple returns",
  "Correlation",
  "Concentration",
  "Volatility & drawdown",
  "Score & stress",
];

const methods = [
  {
    title: "Weight normalization",
    body: "Provided weights are normalized so exposure is measured consistently across the portfolio.",
    formula: "wᵢ = weightᵢ / Σ weightⱼ",
  },
  {
    title: "Aligned price history",
    body: "Historical price series are brought onto a common timeline before any comparison is calculated.",
    formula: "pricesᵢ → common timeline",
  },
  {
    title: "Pearson correlation on simple returns",
    body: "Simple returns are taken from aligned prices, then pairwise Pearson correlation measures how assets move together.",
    formula: "ρᵢⱼ = corr(rᵢ, rⱼ)",
  },
  {
    title: "HHI and effective asset count",
    body: "The Herfindahl-Hirschman Index quantifies concentration; its inverse expresses that concentration as an effective asset count.",
    formula: "HHI = Σ wᵢ²  ·  Neff = 1 / HHI",
  },
  {
    title: "Annualized volatility",
    body: "Return dispersion is annualized to express volatility on a comparable time scale.",
    formula: "σannual = √(wᵀ Σ w)",
  },
  {
    title: "Maximum drawdown",
    body: "The deepest observed peak-to-trough decline in the aligned history is reported as maximum drawdown.",
    formula: "MDD = min(Vt / running max Vt − 1)",
  },
  {
    title: "Hypothetical stress scenarios",
    body: "Hypothetical stress scenarios are applied to current weights to show portfolio sensitivity. Outcomes are illustrations, not forecasts.",
    formula: "scenario + weights → response",
  },
];

const tiers = [
  { range: "0-34", label: "Low", className: "border-positive/35 text-positive" },
  { range: "35-64", label: "Medium", className: "border-gold/40 text-champagne" },
  { range: "65-100", label: "High", className: "border-negative/35 text-negative" },
];

export function TechnologySection() {
  return (
    <section
      id="technology"
      aria-labelledby="technology-heading"
      className="relative border-b border-line/40 bg-secondary/40 py-24 sm:py-32"
    >
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8 lg:px-12">
        <div className="grid gap-12 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)] lg:gap-20">
          <div>
            <p className="auren-eyebrow">02 / Methodology</p>
            <h2
              id="technology-heading"
              className="auren-display mt-6 text-[clamp(2.75rem,4.5vw,4.5rem)] text-primary"
            >
              The mathematics behind the view.
            </h2>
            <p className="mt-7 max-w-md text-base leading-[1.8] text-muted">
              AUREN uses an explicit, rule-based risk engine. Each measure is
              defined from the portfolio you supply, and the same definitions
              are available for review in the documentation.
            </p>

            <div className="mt-12 border-y border-line/60 py-6">
              <p className="auren-eyebrow">Engine sequence</p>
              <ol className="mt-5 flex flex-wrap items-center gap-x-3 gap-y-3">
                {pipeline.map((step, index) => (
                  <li key={step} className="flex items-center gap-3">
                    <span className="border border-line/70 bg-elevated/40 px-2.5 py-1.5 font-mono text-[0.56rem] uppercase tracking-[0.14em] text-muted">
                      {step}
                    </span>
                    {index < pipeline.length - 1 && (
                      <span aria-hidden="true" className="text-gold/50">
                        →
                      </span>
                    )}
                  </li>
                ))}
              </ol>
            </div>
          </div>

          <ol className="border-t border-line/60">
            {methods.map((method, index) => (
              <li
                key={method.title}
                className="grid gap-4 border-b border-line/60 py-7 sm:grid-cols-[2.5rem_minmax(0,1fr)] lg:grid-cols-[2.5rem_minmax(0,1fr)_minmax(0,0.8fr)] lg:gap-8"
              >
                <span className="font-mono text-[0.65rem] text-gold/70">
                  0{index + 1}
                </span>
                <div>
                  <h3 className="font-display text-2xl leading-tight text-primary sm:text-3xl">
                    {method.title}
                  </h3>
                  <p className="mt-3 max-w-xl text-sm leading-relaxed text-muted">
                    {method.body}
                  </p>
                </div>
                <p className="self-center font-mono text-[0.68rem] leading-relaxed text-champagne/80 lg:text-right">
                  {method.formula}
                </p>
              </li>
            ))}
          </ol>
        </div>

        <div className="mt-20 border-t border-line/60 pt-12">
          <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="auren-eyebrow">Score classification</p>
              <h3 className="auren-display mt-4 text-4xl text-primary sm:text-5xl">
                Rule-based score tiers
              </h3>
            </div>
            <p className="max-w-md text-sm leading-relaxed text-muted">
              The composite score is mapped to a tier with fixed thresholds, so
              the same inputs always produce the same classification.
            </p>
          </div>

          <div className="mt-10 grid gap-px border border-line/60 bg-line/60 sm:grid-cols-3">
            {tiers.map((tier) => (
              <div key={tier.label} className="bg-secondary px-6 py-7">
                <p className="font-mono text-[0.62rem] uppercase tracking-[0.2em] text-faint">
                  Score
                </p>
                <p className="mt-3 font-display text-4xl leading-none text-primary">
                  {tier.range}
                </p>
                <p
                  className={cn(
                    "mt-5 inline-flex border px-2.5 py-1 font-mono text-[0.6rem] uppercase tracking-[0.2em]",
                    tier.className
                  )}
                >
                  {tier.label}
                </p>
              </div>
            ))}
          </div>

          <p className="mt-6 font-mono text-[0.6rem] uppercase leading-relaxed tracking-[0.16em] text-faint">
            Stress scenario results are hypothetical and depend on the scenario
            applied. They are not predictions.
          </p>
        </div>
      </div>
    </section>
  );
}

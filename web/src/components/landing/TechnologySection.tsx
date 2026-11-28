export function TechnologySection() {
  const methods = [
    {
      title: "Weight Normalization",
      body: "Raw position balances are normalized so factor and issuer exposures sum to 1.0 across all asset classes.",
      formula: "w_i = asset_i / Σ asset_j",
    },
    {
      title: "Aligned Daily History",
      body: "Disparate price feeds are aligned along common trading timestamps prior to statistical transformation.",
      formula: "prices_i → common timeline",
    },
    {
      title: "Pairwise Pearson Correlation",
      body: "Simple percentage returns calculate mutual linear correlation across the aligned timeline.",
      formula: "ρ_{ij} = Cov(r_i, r_j) / (σ_i · σ_j)",
    },
    {
      title: "HHI & Effective Diversification",
      body: "The Herfindahl-Hirschman Index measures concentration; inverse HHI represents the effective number of independent bets.",
      formula: "HHI = Σ w_i²  ·  Neff = 1 / HHI",
    },
    {
      title: "Annualized Historical Volatility",
      body: "Return standard deviation is scaled by trading frequency (√252) to produce comparable institutional volatility.",
      formula: "σ_annual = √(wᵀ Σ w)",
    },
    {
      title: "Peak-to-Trough Drawdown",
      body: "Continuous high-water mark tracking identifies deepest observed portfolio equity declines.",
      formula: "MDD = min(V_t / max(V_{0...t}) - 1)",
    },
  ];

  return (
    <section
      id="technology"
      aria-labelledby="technology-heading"
      className="border-b border-line bg-obsidian py-16 sm:py-24"
    >
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8 lg:px-12">
        <div className="max-w-2xl">
          <span className="font-mono text-xs font-semibold uppercase tracking-wider text-gold">
            QUANTITATIVE METHODOLOGY
          </span>
          <h2
            id="technology-heading"
            className="mt-3 font-sans text-3xl font-bold tracking-tight text-primary sm:text-4xl"
          >
            Audited, rule-based mathematical models.
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-muted sm:text-base">
            No black-box guesses. Every metric is computed deterministically from transparent formulas available in full detail.
          </p>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {methods.map((method, index) => (
            <div
              key={method.title}
              className="flex flex-col justify-between rounded-xl border border-line bg-secondary p-6"
            >
              <div>
                <span className="font-mono text-xs font-medium text-gold">
                  0{index + 1}
                </span>
                <h3 className="mt-3 font-sans text-base font-semibold text-primary">
                  {method.title}
                </h3>
                <p className="mt-2 text-xs leading-relaxed text-muted">
                  {method.body}
                </p>
              </div>
              <div className="mt-5 rounded-md border border-line bg-elevated px-3 py-2">
                <code className="font-mono text-[0.7rem] text-champagne">
                  {method.formula}
                </code>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

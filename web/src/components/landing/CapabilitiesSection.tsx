const capabilities = [
  {
    title: "Portfolio Risk Assessment",
    description:
      "Read a composite risk score alongside the concentration, correlation, volatility, and drawdown measures that produce it.",
  },
  {
    title: "Asset Exposure",
    description:
      "Break allocation down by asset and sector to see where capital is actually concentrated.",
  },
  {
    title: "Correlation Analysis",
    description:
      "Inspect pairwise relationships on aligned simple returns to understand how holdings move together.",
  },
  {
    title: "Historical Stress Testing",
    description:
      "Apply hypothetical historical market shocks to the current portfolio and review the resulting impact.",
  },
  {
    title: "AI Verification",
    description:
      "Generate a written report from computed metrics. When verification is configured, numbers that cannot be matched to analysis outputs are flagged; it is not a guarantee of correctness.",
  },
  {
    title: "Proof and API Transparency",
    description:
      "Trace each metric back to its definition and access the same calculations programmatically through the API.",
  },
];

function Motif({ index }: { index: number }) {
  const shared = {
    "aria-hidden": true,
    viewBox: "0 0 72 72",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1,
    className:
      "h-16 w-16 text-gold/45 transition-colors duration-500 group-hover:text-champagne",
  } as const;

  if (index === 0) {
    return (
      <svg {...shared}>
        <path d="M36 8 64 36 36 64 8 36 36 8Z" />
        <path d="M36 20 52 36 36 52 20 36 36 20Z" />
        <circle cx="36" cy="36" r="3.5" fill="currentColor" stroke="none" />
      </svg>
    );
  }
  if (index === 1) {
    return (
      <svg {...shared}>
        <rect x="12" y="12" width="48" height="48" />
        <rect x="22" y="22" width="28" height="28" />
        <rect x="31" y="31" width="10" height="10" />
      </svg>
    );
  }
  if (index === 2) {
    return (
      <svg {...shared}>
        {[18, 36, 54].map((x) =>
          [18, 36, 54].map((y) => (
            <circle key={`${x}-${y}`} cx={x} cy={y} r="2.5" fill="currentColor" stroke="none" />
          ))
        )}
        <path d="M18 18h36v36H18z" opacity="0.35" />
      </svg>
    );
  }
  if (index === 3) {
    return (
      <svg {...shared}>
        <path d="M8 36h12l8-16 10 32 8-16h18" />
        <path d="M8 48h56" strokeDasharray="3 5" opacity="0.5" />
      </svg>
    );
  }
  if (index === 4) {
    return (
      <svg {...shared}>
        <path d="M22 10h22l10 10v42H22V10Z" />
        <path d="M44 10v10h10" />
        <path d="m30 42 6 6 10-12" />
      </svg>
    );
  }
  return (
    <svg {...shared}>
      <path d="M28 14c-8 0-8 8-8 12s0 8-6 10c6 2 6 6 6 10s0 12 8 12" />
      <path d="M44 14c8 0 8 8 8 12s0 8 6 10c-6 2-6 6-6 10s0 12-8 12" />
      <circle cx="36" cy="36" r="2.5" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function CapabilitiesSection() {
  return (
    <section
      id="capabilities"
      aria-labelledby="capabilities-heading"
      className="relative border-b border-line/40 bg-obsidian py-24 sm:py-32"
    >
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8 lg:px-12">
        <div className="max-w-3xl">
          <p className="auren-eyebrow">03 / Capabilities</p>
          <h2
            id="capabilities-heading"
            className="auren-display mt-6 text-[clamp(2.75rem,4.5vw,4.5rem)] text-primary"
          >
            Every layer, in one view.
          </h2>
          <p className="mt-7 text-base leading-[1.8] text-muted">
            Six connected ways into the same portfolio, each built on the same
            transparent calculation engine.
          </p>
        </div>

        <ol className="mt-14 border-t border-line/60">
          {capabilities.map((capability, index) => (
            <li
              key={capability.title}
              className="group grid gap-5 border-b border-line/60 py-9 lg:grid-cols-[3rem_minmax(0,0.9fr)_minmax(0,1.1fr)_5rem] lg:items-center lg:gap-8"
            >
              <span className="font-mono text-[0.65rem] text-gold/70">
                0{index + 1}
              </span>
              <h3 className="font-display text-3xl leading-tight text-primary sm:text-4xl">
                {capability.title}
              </h3>
              <p className="max-w-xl text-sm leading-relaxed text-muted">
                {capability.description}
              </p>
              <div className="flex lg:justify-end">
                <Motif index={index} />
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

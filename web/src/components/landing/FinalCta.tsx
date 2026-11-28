import { ArrowUpRight } from "lucide-react";
import { ButtonLink } from "@/components/ui/Button";

export function FinalCta() {
  return (
    <section
      aria-labelledby="final-cta-heading"
      className="border-b border-line bg-secondary py-20 lg:py-28"
    >
      <div className="mx-auto max-w-3xl px-5 text-center sm:px-8">
        <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-elevated px-3 py-1 font-mono text-[0.65rem] font-medium tracking-wider text-gold">
          GET STARTED
        </span>
        <h2
          id="final-cta-heading"
          className="mt-6 font-sans text-3xl font-bold tracking-tight text-primary sm:text-4xl lg:text-5xl"
        >
          Institutional risk intelligence. Zero guesswork.
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-sm leading-relaxed text-muted sm:text-base">
          Analyze single portfolios, run stress tests against macro shocks, and access transparent calculations via the AUREN API.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <ButtonLink href="/dashboard" className="px-5 py-2.5 text-xs font-semibold">
            Open Workstation
            <ArrowUpRight aria-hidden="true" className="h-4 w-4" />
          </ButtonLink>
          <ButtonLink href="/dashboard?tab=docs" variant="secondary" className="px-5 py-2.5 text-xs">
            Explore Documentation
          </ButtonLink>
        </div>
      </div>
    </section>
  );
}

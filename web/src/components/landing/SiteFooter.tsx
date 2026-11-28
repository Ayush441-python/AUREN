import Link from "next/link";
import { Wordmark } from "@/components/ui/Wordmark";

const footerLinks = [
  { label: "Overview", href: "/dashboard" },
  { label: "Factor Exposure", href: "/dashboard?tab=exposure" },
  { label: "Correlation Matrix", href: "/dashboard?tab=correlation" },
  { label: "Stress Testing", href: "/dashboard?tab=stress" },
  { label: "AI Verification", href: "/dashboard?tab=report" },
  { label: "Documentation & API", href: "/dashboard?tab=docs" },
];

export function SiteFooter() {
  return (
    <footer className="bg-obsidian py-12 sm:py-16">
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8 lg:px-12">
        <div className="flex flex-col gap-10 md:flex-row md:items-start md:justify-between">
          <div>
            <Wordmark />
            <p className="mt-3 max-w-sm text-xs leading-relaxed text-muted">
              Institutional-grade portfolio risk decomposition and deterministic scenario stress modeling.
            </p>
          </div>

          <nav aria-label="Footer Navigation">
            <span className="font-mono text-[0.68rem] font-medium uppercase tracking-wider text-muted">
              Platform Modules
            </span>
            <ul className="mt-3 grid grid-cols-2 gap-x-8 gap-y-2.5 sm:grid-cols-3">
              {footerLinks.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-xs text-muted transition-colors hover:text-champagne"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        <div className="mt-12 flex flex-col gap-3 border-t border-line pt-6 text-[0.7rem] text-faint sm:flex-row sm:items-center sm:justify-between">
          <p>Strictly for informational and analytical purposes. Not investment advice.</p>
          <p className="font-mono">AUREN RISK INTELLIGENCE</p>
        </div>
      </div>
    </footer>
  );
}

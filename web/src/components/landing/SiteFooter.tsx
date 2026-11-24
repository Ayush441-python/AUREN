import Link from "next/link";
import { Wordmark } from "@/components/ui/Wordmark";

const footerLinks = [
  { label: "Product", href: "#architecture" },
  { label: "Technology", href: "#technology" },
  { label: "Features", href: "#capabilities" },
  { label: "Documentation", href: "/dashboard?tab=docs" },
];

export function SiteFooter() {
  return (
    <footer className="bg-obsidian py-14 sm:py-20">
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8 lg:px-12">
        <div className="flex flex-col gap-12 md:flex-row md:items-start md:justify-between">
          <div>
            <Link href="#main" aria-label="AUREN, skip to content">
              <Wordmark />
            </Link>
            <p className="mt-5 max-w-xs text-sm leading-relaxed text-muted">
              Portfolio risk intelligence through transparent, quantitative
              analysis.
            </p>
          </div>

          <nav aria-label="Footer">
            <p className="auren-eyebrow">Navigate</p>
            <ul className="mt-5 grid grid-cols-2 gap-x-10 gap-y-4 sm:gap-x-16">
              {footerLinks.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="font-mono text-[0.62rem] uppercase tracking-[0.16em] text-muted transition-colors duration-300 hover:text-champagne"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        <div className="mt-14 flex flex-col gap-3 border-t border-line/60 pt-7 sm:flex-row sm:items-center sm:justify-between">
          <p className="font-mono text-[0.58rem] uppercase tracking-[0.18em] text-faint">
            Analytics only, not investment advice.
          </p>
          <p className="font-mono text-[0.58rem] uppercase tracking-[0.18em] text-faint">
            AUREN / Risk Intelligence
          </p>
        </div>
      </div>
    </footer>
  );
}

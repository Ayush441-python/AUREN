"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowUpRight, Menu, X } from "lucide-react";
import { ButtonLink } from "@/components/ui/Button";
import { Wordmark } from "@/components/ui/Wordmark";

const navLinks = [
  { label: "Capabilities", href: "#capabilities" },
  { label: "Methodology", href: "#technology" },
  { label: "API & Proof", href: "/dashboard?tab=docs" },
];

export function LandingNav() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-line bg-[#0B0D0F]/90 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-[1400px] items-center justify-between px-5 sm:px-8 lg:px-12">
        <Link href="/" className="shrink-0">
          <Wordmark />
        </Link>

        <nav aria-label="Primary" className="hidden items-center gap-6 md:flex">
          {navLinks.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className="text-xs font-medium text-muted transition-colors hover:text-primary"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <ButtonLink href="/dashboard" className="px-3.5 py-1.5 text-xs font-semibold">
            Launch Workstation
            <ArrowUpRight aria-hidden="true" className="h-3.5 w-3.5" />
          </ButtonLink>
        </div>

        <button
          type="button"
          aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
          onClick={() => setMenuOpen((open) => !open)}
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-line text-muted transition-colors hover:text-primary md:hidden"
        >
          {menuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        </button>
      </div>

      {menuOpen && (
        <div className="border-t border-line bg-secondary px-5 py-4 md:hidden">
          <nav className="flex flex-col gap-3">
            {navLinks.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                onClick={() => setMenuOpen(false)}
                className="text-sm font-medium text-muted hover:text-primary"
              >
                {link.label}
              </Link>
            ))}
            <ButtonLink
              href="/dashboard"
              onClick={() => setMenuOpen(false)}
              className="mt-2 w-full text-xs font-semibold"
            >
              Launch Workstation
              <ArrowUpRight className="h-3.5 w-3.5" />
            </ButtonLink>
          </nav>
        </div>
      )}
    </header>
  );
}

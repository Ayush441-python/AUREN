"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowUpRight, Menu, X } from "lucide-react";
import { ButtonLink } from "@/components/ui/Button";
import { Wordmark } from "@/components/ui/Wordmark";

const navLinks = [
  { label: "Product", href: "#architecture" },
  { label: "Technology", href: "#technology" },
  { label: "Features", href: "#capabilities" },
  { label: "Documentation", href: "/dashboard?tab=docs" },
];

const desktopLinkClass =
  "border-b border-transparent py-1 font-mono text-[0.66rem] uppercase tracking-[0.2em] text-muted transition-colors duration-300 hover:border-gold/60 hover:text-champagne";

export function LandingNav() {
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (!menuOpen) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMenuOpen(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [menuOpen]);

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-line/60 bg-obsidian/85 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-[1400px] items-center justify-between gap-6 px-5 sm:px-8 lg:px-12">
        <Link href="#main" aria-label="AUREN, skip to content" className="shrink-0">
          <Wordmark />
        </Link>

        <nav aria-label="Primary" className="hidden items-center gap-8 lg:flex">
          {navLinks.map((link) => (
            <Link key={link.label} href={link.href} className={desktopLinkClass}>
              {link.label}
            </Link>
          ))}
        </nav>

        <ButtonLink href="/dashboard" className="hidden px-4 py-2 lg:inline-flex">
          Launch App
          <ArrowUpRight aria-hidden="true" className="h-3.5 w-3.5" />
        </ButtonLink>

        <button
          type="button"
          aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={menuOpen}
          aria-controls="landing-mobile-menu"
          onClick={() => setMenuOpen((open) => !open)}
          className="inline-flex h-10 w-10 items-center justify-center border border-line text-muted transition-colors duration-300 hover:border-gold/50 hover:text-champagne lg:hidden"
        >
          {menuOpen ? (
            <X aria-hidden="true" className="h-4 w-4" />
          ) : (
            <Menu aria-hidden="true" className="h-4 w-4" />
          )}
        </button>
      </div>

      <div
        id="landing-mobile-menu"
        hidden={!menuOpen}
        className="border-t border-line/60 bg-obsidian/95 backdrop-blur-xl"
      >
        <nav
          aria-label="Mobile"
          className="mx-auto flex max-w-[1400px] flex-col px-5 py-5 sm:px-8 lg:hidden"
        >
          {navLinks.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              onClick={() => setMenuOpen(false)}
              className="border-b border-line/40 py-3 font-display text-2xl leading-none text-primary transition-colors duration-300 hover:text-champagne"
            >
              {link.label}
            </Link>
          ))}
          <ButtonLink
            href="/dashboard"
            onClick={() => setMenuOpen(false)}
            className="mt-5 w-full"
          >
            Launch App
            <ArrowUpRight aria-hidden="true" className="h-3.5 w-3.5" />
          </ButtonLink>
        </nav>
      </div>
    </header>
  );
}

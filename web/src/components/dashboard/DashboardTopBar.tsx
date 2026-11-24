"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import {
  ArrowUpRight,
  ChevronDown,
  Layers3,
  Plus,
  ShieldAlert,
  Wallet,
} from "lucide-react";
import { PRESETS } from "@/lib/presets";
import { cn } from "@/lib/cn";
import type { DataStatus, DashboardTab } from "@/components/dashboard/Workstation";

interface DashboardTopBarProps {
  portfolioName: string;
  portfolioId?: string;
  activeTab: DashboardTab;
  dataStatus: DataStatus;
  loading: boolean;
  walletAddress: string | null;
  onNewPortfolio: () => void;
  onOpenWallet: () => void;
  onOpenBuilder: () => void;
  onApplyPreset: (weights: Record<string, number>, name: string) => void;
}

const statusLabel: Record<DataStatus, string> = {
  reference: "Reference",
  live: "Live",
  stale: "Previous",
};

export function DashboardTopBar({
  portfolioName,
  portfolioId,
  activeTab,
  dataStatus,
  loading,
  walletAddress,
  onNewPortfolio,
  onOpenWallet,
  onOpenBuilder,
  onApplyPreset,
}: DashboardTopBarProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  const presets = useMemo(
    () =>
      Object.entries(PRESETS).map(([key, preset]) => {
        const total = preset.holdings.reduce((sum, [, weight]) => sum + weight, 0) || 1;
        const weights: Record<string, number> = {};
        preset.holdings.forEach(([ticker, weight]) => {
          weights[ticker] = weight / total;
        });
        return {
          key,
          name: preset.name,
          description: preset.description,
          weights,
          count: preset.holdings.length,
        };
      }),
    []
  );

  useEffect(() => {
    if (!menuOpen) return;
    const onPointerDown = (event: PointerEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMenuOpen(false);
        triggerRef.current?.focus();
      }
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [menuOpen]);

  const applyPreset = (weights: Record<string, number>, name: string) => {
    setMenuOpen(false);
    onApplyPreset(weights, name);
  };

  return (
    <header className="sticky top-0 z-30 flex min-h-16 w-full flex-wrap items-center justify-between gap-3 border-b border-line bg-obsidian/90 px-4 py-3 backdrop-blur-md sm:px-6 lg:px-10">
      <div className="flex min-w-0 items-center gap-2.5 sm:gap-4">
        <div ref={menuRef} className="relative min-w-0">
          <button
            ref={triggerRef}
            type="button"
            onClick={() => setMenuOpen((value) => !value)}
            aria-haspopup="menu"
            aria-expanded={menuOpen}
            aria-controls="portfolio-context-menu"
            className="flex max-w-[62vw] items-center gap-2.5 border border-line bg-elevated/70 px-3 py-2 text-left transition-colors hover:border-gold/50 focus-visible:border-gold sm:max-w-xs"
          >
            <Layers3 aria-hidden="true" className="h-3.5 w-3.5 shrink-0 text-gold" />
            <span className="min-w-0">
              <span className="block font-mono text-[0.56rem] uppercase tracking-[0.18em] text-faint">
                {portfolioId ? `Portfolio ${portfolioId}` : "Active workspace"}
              </span>
              <span className="block truncate text-xs text-primary" title={portfolioName}>
                {portfolioName}
              </span>
            </span>
            <ChevronDown
              aria-hidden="true"
              className={cn("h-3.5 w-3.5 shrink-0 text-muted transition-transform", menuOpen && "rotate-180")}
            />
          </button>

          {menuOpen && (
            <div
              id="portfolio-context-menu"
              role="menu"
              aria-label="Portfolio presets"
              className="absolute left-0 top-[calc(100%+8px)] z-50 w-[min(88vw,360px)] border border-line bg-secondary p-1.5 shadow-2xl"
            >
              <p className="auren-eyebrow px-2.5 py-2">Institutional presets</p>
              <div className="max-h-72 overflow-y-auto">
                {presets.map((preset) => (
                  <button
                    key={preset.key}
                    type="button"
                    role="menuitem"
                    onClick={() => applyPreset(preset.weights, preset.name)}
                    className="block w-full border border-transparent px-2.5 py-2 text-left transition-colors hover:border-line hover:bg-elevated"
                  >
                    <span className="flex items-center justify-between gap-3">
                      <span className="truncate text-xs text-primary">{preset.name}</span>
                      <span className="shrink-0 font-mono text-[0.58rem] text-faint">
                        {preset.count} assets
                      </span>
                    </span>
                    <span className="mt-1 block truncate text-[0.68rem] text-muted">
                      {preset.description}
                    </span>
                  </button>
                ))}
              </div>
              <div className="mt-1 border-t border-line pt-1">
                <button
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    setMenuOpen(false);
                    onOpenBuilder();
                  }}
                  className="flex w-full items-center gap-2 px-2.5 py-2 text-left font-mono text-[0.62rem] uppercase tracking-[0.16em] text-champagne transition-colors hover:bg-elevated"
                >
                  <Plus aria-hidden="true" className="h-3.5 w-3.5" />
                  Build custom allocation
                </button>
              </div>
            </div>
          )}
        </div>

        <span
          className={cn(
            "hidden items-center gap-1.5 border px-2.5 py-1 font-mono text-[0.58rem] uppercase tracking-[0.16em] md:inline-flex",
            dataStatus === "live" && "border-positive/30 bg-positive/5 text-positive",
            dataStatus === "reference" && "border-line bg-elevated/60 text-muted",
            dataStatus === "stale" && "border-negative/30 bg-negative/5 text-negative"
          )}
        >
          <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-current" />
          {statusLabel[dataStatus]}
        </span>
        <span className="hidden font-mono text-[0.58rem] uppercase tracking-[0.18em] text-faint xl:inline">
          {activeTab}
        </span>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <Link
          href="/"
          className="hidden items-center gap-1 border border-line px-2.5 py-2 font-mono text-[0.58rem] uppercase tracking-[0.16em] text-muted transition-colors hover:border-gold/50 hover:text-highlight lg:inline-flex"
        >
          Site
          <ArrowUpRight aria-hidden="true" className="h-3 w-3" />
        </Link>

        <div className="hidden items-center gap-1.5 border border-line bg-elevated/50 px-2.5 py-2 text-[0.62rem] text-muted sm:flex">
          <ShieldAlert aria-hidden="true" className="h-3.5 w-3.5 text-gold" />
          <span>Analytics only, not investment advice</span>
        </div>

        <button
          type="button"
          onClick={onOpenWallet}
          aria-label={walletAddress ? `Wallet ${walletAddress} options` : "Connect wallet"}
          className={cn(
            "inline-flex items-center gap-2 border px-2.5 py-2 font-mono text-[0.62rem] uppercase tracking-[0.14em] transition-colors",
            walletAddress
              ? "border-positive/35 bg-positive/5 text-positive hover:border-positive/60"
              : "border-line bg-elevated/60 text-primary hover:border-gold/50"
          )}
        >
          <Wallet aria-hidden="true" className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">
            {walletAddress ? `${walletAddress.slice(0, 6)}...${walletAddress.slice(-4)}` : "Wallet"}
          </span>
        </button>

        <button
          type="button"
          onClick={onNewPortfolio}
          className="inline-flex items-center gap-2 border border-gold/60 bg-gold/15 px-2.5 py-2 font-mono text-[0.62rem] uppercase tracking-[0.14em] text-highlight transition-colors hover:bg-gold/25"
        >
          {loading ? (
            <span
              aria-hidden="true"
              className="auren-spin h-3.5 w-3.5 rounded-full border border-gold/30 border-t-gold"
            />
          ) : (
            <Plus aria-hidden="true" className="h-3.5 w-3.5" />
          )}
          <span className="hidden sm:inline">New Portfolio</span>
          <span className="sm:hidden">New</span>
        </button>
      </div>

      <p className="w-full text-[0.62rem] text-faint sm:hidden">
        Analytics only, not investment advice
      </p>
      <span aria-live="polite" className="sr-only">
        {loading ? "Recalculating risk analysis" : ""}
      </span>
    </header>
  );
}

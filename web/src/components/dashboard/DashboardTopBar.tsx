"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import {
  ArrowUpRight,
  ChevronDown,
  Layers3,
  Plus,
  Share2,
  Wallet,
  Zap,
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
  onOpenAttest?: () => void;
  onOpenShare?: () => void;
  onApplyPreset: (weights: Record<string, number>, name: string) => void;
}

const statusLabel: Record<DataStatus, string> = {
  reference: "Reference Dataset",
  live: "Live Engine",
  stale: "Previous Calculation",
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
  onOpenAttest,
  onOpenShare,
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
    window.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [menuOpen]);

  return (
    <header className="sticky top-0 z-30 border-b border-line bg-secondary/95 backdrop-blur-md">
      <div className="flex h-14 items-center justify-between gap-3 px-3 sm:px-6">
        {/* Left: Active Portfolio Indicator & Engine Status */}
        <div className="flex min-w-0 shrink items-center gap-2.5">
          <div className="relative shrink-0" ref={menuRef}>
            <button
              ref={triggerRef}
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              className="flex items-center gap-2 rounded-lg border border-line bg-elevated px-3 py-1.5 text-xs font-semibold text-primary transition-colors hover:border-gold/40"
            >
              <Layers3 className="h-3.5 w-3.5 text-gold shrink-0" />
              <span className="max-w-[130px] truncate sm:max-w-[200px] md:max-w-[240px]">
                {portfolioName}
              </span>
              <ChevronDown className="h-3 w-3 text-muted shrink-0" />
            </button>

            {menuOpen && (
              <div
                role="menu"
                className="absolute left-0 top-full mt-1.5 w-72 rounded-lg border border-line bg-secondary p-1.5 shadow-xl z-50"
              >
                <div className="px-2.5 py-1.5 text-[0.65rem] font-mono font-semibold uppercase tracking-wider text-muted border-b border-line mb-1">
                  Institutional Benchmark Portfolios
                </div>
                {presets.map((preset) => (
                  <button
                    key={preset.key}
                    type="button"
                    role="menuitem"
                    onClick={() => {
                      onApplyPreset(preset.weights, preset.name);
                      setMenuOpen(false);
                    }}
                    className="flex w-full flex-col rounded-md px-2.5 py-2 text-left text-xs transition-colors hover:bg-elevated hover:text-primary"
                  >
                    <span className="font-semibold text-primary">{preset.name}</span>
                    <span className="mt-0.5 line-clamp-1 text-[0.68rem] text-muted">
                      {preset.description}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Engine Status Badge - hide on small/medium screens to prevent pushing buttons */}
          <div className="hidden 2xl:flex items-center gap-1.5 shrink-0 rounded-md border border-line bg-elevated px-2.5 py-1 font-mono text-[0.65rem] whitespace-nowrap">
            <span
              className={cn(
                "h-1.5 w-1.5 rounded-full shrink-0",
                dataStatus === "live" && "bg-positive",
                dataStatus === "reference" && "bg-muted",
                dataStatus === "stale" && "bg-negative"
              )}
            />
            <span className="text-muted">{statusLabel[dataStatus]}</span>
          </div>

          {loading && (
            <span className="hidden xl:flex items-center gap-1.5 font-mono text-[0.65rem] text-gold animate-pulse whitespace-nowrap shrink-0">
              Computing risk matrix...
            </span>
          )}
        </div>

        {/* Right Action Tools - flex with shrink-0 so it never overlaps left items */}
        <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
          {onOpenAttest && (
            <button
              type="button"
              onClick={onOpenAttest}
              className="flex h-8 items-center gap-1.5 whitespace-nowrap rounded-lg border border-gold/50 bg-gold/15 px-2.5 sm:px-3 text-xs font-semibold text-highlight transition-all hover:border-gold hover:bg-gold/25"
            >
              <Zap className="h-3.5 w-3.5 text-gold shrink-0" />
              <span className="hidden sm:inline">Attest On-Chain</span>
            </button>
          )}

          {onOpenShare && (
            <button
              type="button"
              onClick={onOpenShare}
              className="hidden md:flex h-8 items-center gap-1.5 whitespace-nowrap rounded-lg border border-line bg-elevated px-2.5 sm:px-3 text-xs font-medium text-primary transition-all hover:border-gold/40 hover:bg-[#1f242c]"
            >
              <Share2 className="h-3.5 w-3.5 text-gold shrink-0" />
              <span className="hidden xl:inline">Share to X</span>
            </button>
          )}

          <button
            type="button"
            onClick={onOpenBuilder}
            className="flex h-8 items-center gap-1.5 whitespace-nowrap rounded-lg border border-line bg-elevated px-2.5 sm:px-3 text-xs font-medium text-primary transition-all hover:border-gold/40 hover:bg-[#1f242c]"
          >
            <Plus className="h-3.5 w-3.5 text-gold shrink-0" />
            <span className="hidden sm:inline">Custom Portfolio</span>
          </button>

          <button
            type="button"
            onClick={onOpenWallet}
            className="flex h-8 items-center gap-1.5 whitespace-nowrap rounded-lg border border-line bg-elevated px-2.5 sm:px-3 text-xs font-medium text-primary transition-all hover:border-gold/40 hover:bg-[#1f242c]"
          >
            <Wallet className="h-3.5 w-3.5 text-gold shrink-0" />
            <span className="hidden sm:inline font-mono">
              {walletAddress ? `${walletAddress.slice(0, 6)}...${walletAddress.slice(-4)}` : "Connect Wallet"}
            </span>
          </button>

          <Link
            href="/"
            className="hidden xl:flex h-8 items-center gap-1 whitespace-nowrap rounded-lg border border-line px-2.5 text-xs text-muted transition-all hover:text-primary hover:border-gold/40"
            title="Return to site"
          >
            <span className="text-[0.7rem]">Exit</span>
            <ArrowUpRight className="h-3 w-3 shrink-0" />
          </Link>
        </div>
      </div>
    </header>
  );
}

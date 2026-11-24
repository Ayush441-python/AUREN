"use client";

import { useState, type ReactNode } from "react";
import Link from "next/link";
import { ArrowUpRight, X } from "lucide-react";
import { cn } from "@/lib/cn";
import type { DataStatus, DashboardTab } from "@/components/dashboard/Workstation";
import { CompactSidebar } from "@/components/dashboard/CompactSidebar";
import { DashboardTopBar } from "@/components/dashboard/DashboardTopBar";
import { MobileTabs } from "@/components/dashboard/MobileTabs";

interface DashboardShellProps {
  activeTab: DashboardTab;
  onSelectTab: (tab: DashboardTab) => void;
  portfolioName: string;
  portfolioId?: string;
  dataStatus: DataStatus;
  loading: boolean;
  error: string | null;
  walletAddress: string | null;
  onNewPortfolio: () => void;
  onOpenWallet: () => void;
  onOpenBuilder: () => void;
  onApplyPreset: (weights: Record<string, number>, name: string) => void;
  onDismissError: () => void;
  children: ReactNode;
}

const statusCopy: Record<DataStatus, string> = {
  reference: "Reference dataset",
  live: "Live analysis",
  stale: "Previous analysis",
};

export function DashboardShell({
  activeTab,
  onSelectTab,
  portfolioName,
  portfolioId,
  dataStatus,
  loading,
  error,
  walletAddress,
  onNewPortfolio,
  onOpenWallet,
  onOpenBuilder,
  onApplyPreset,
  onDismissError,
  children,
}: DashboardShellProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="min-h-screen w-full overflow-x-hidden bg-obsidian text-primary">
      <a
        href="#dashboard-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[120] focus:border focus:border-gold focus:bg-elevated focus:px-4 focus:py-2 focus:text-xs focus:text-highlight"
      >
        Skip to analysis
      </a>

      <CompactSidebar
        activeTab={activeTab}
        onSelectTab={onSelectTab}
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed((value) => !value)}
        portfolioLabel={portfolioName}
        dataStatus={dataStatus}
      />

      <div
        className={cn(
          "flex min-w-0 flex-col transition-[padding] duration-300",
          collapsed ? "lg:pl-[72px]" : "lg:pl-[72px] xl:pl-[244px]"
        )}
      >
        <DashboardTopBar
          portfolioName={portfolioName}
          portfolioId={portfolioId}
          activeTab={activeTab}
          dataStatus={dataStatus}
          loading={loading}
          walletAddress={walletAddress}
          onNewPortfolio={onNewPortfolio}
          onOpenWallet={onOpenWallet}
          onOpenBuilder={onOpenBuilder}
          onApplyPreset={onApplyPreset}
        />

        <main
          id="dashboard-content"
          className="min-w-0 flex-1 px-4 pb-28 pt-8 sm:px-6 lg:px-10 lg:pb-12"
        >
          <div className="mx-auto w-full max-w-[1440px] space-y-7">
            <div
              aria-live="polite"
              className="flex flex-wrap items-center justify-between gap-3 border-b border-line/70 pb-4"
            >
              <div className="flex flex-wrap items-center gap-3">
                <span className="auren-eyebrow">Workstation / {activeTab}</span>
                <span
                  className={cn(
                    "inline-flex items-center gap-2 border px-2.5 py-1 font-mono text-[0.6rem] uppercase tracking-[0.18em]",
                    dataStatus === "live" && "border-positive/35 bg-positive/10 text-positive",
                    dataStatus === "reference" && "border-line bg-elevated/70 text-muted",
                    dataStatus === "stale" && "border-negative/35 bg-negative/10 text-negative"
                  )}
                >
                  <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-current" />
                  {statusCopy[dataStatus]}
                </span>
                {loading && (
                  <span className="inline-flex items-center gap-2 font-mono text-[0.6rem] uppercase tracking-[0.18em] text-champagne">
                    <span
                      aria-hidden="true"
                      className="auren-spin h-3 w-3 rounded-full border border-gold/30 border-t-gold"
                    />
                    Recalculating
                  </span>
                )}
              </div>
              <Link
                href="/"
                className="inline-flex items-center gap-1.5 font-mono text-[0.62rem] uppercase tracking-[0.18em] text-muted transition-colors hover:text-champagne"
              >
                Return to site
                <ArrowUpRight className="h-3.5 w-3.5" aria-hidden="true" />
              </Link>
            </div>

            {error && (
              <div
                role="alert"
                className="flex items-start justify-between gap-4 border border-negative/30 bg-negative/5 px-4 py-3"
              >
                <div className="min-w-0">
                  <p className="font-mono text-[0.62rem] uppercase tracking-[0.2em] text-negative">
                    Analysis status
                  </p>
                  <p className="mt-1.5 text-xs leading-relaxed text-primary">{error}</p>
                </div>
                <button
                  type="button"
                  onClick={onDismissError}
                  aria-label="Dismiss status message"
                  className="border border-line p-1.5 text-muted transition-colors hover:border-gold/50 hover:text-highlight"
                >
                  <X className="h-3.5 w-3.5" aria-hidden="true" />
                </button>
              </div>
            )}

            {children}
          </div>
        </main>
      </div>

      <MobileTabs activeTab={activeTab} onSelectTab={onSelectTab} />
    </div>
  );
}

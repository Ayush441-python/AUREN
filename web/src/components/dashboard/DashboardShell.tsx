"use client";

import { type ReactNode } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/cn";
import type { DataStatus } from "@/components/dashboard/Workstation";
import { AurenSidebar } from "@/components/navigation/AurenSidebar";
import { SidebarToggle } from "@/components/navigation/SidebarToggle";
import { DashboardTopBar } from "@/components/dashboard/DashboardTopBar";
import { useNavigation } from "@/lib/navigationContext";
import type { NavItemKey } from "@/lib/navigationTypes";

interface DashboardShellProps {
  activeTab: NavItemKey;
  onSelectTab: (tab: NavItemKey) => void;
  portfolioName: string;
  portfolioId?: string;
  dataStatus: DataStatus;
  loading: boolean;
  error: string | null;
  walletAddress: string | null;
  onNewPortfolio: () => void;
  onOpenWallet: () => void;
  onOpenBuilder: () => void;
  onOpenAttest?: () => void;
  onOpenShare?: () => void;
  onApplyPreset: (weights: Record<string, number>, name: string) => void;
  onDismissError: () => void;
  children: ReactNode;
}

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
  onOpenAttest,
  onOpenShare,
  onApplyPreset,
  onDismissError,
  children,
}: DashboardShellProps) {
  const { isCollapsed } = useNavigation();

  return (
    <div className="min-h-screen w-full bg-[#0A0C0E] text-[#F4F2ED]">
      {/* Original Modern Collapsible Sidebar & Mobile Drawer */}
      <AurenSidebar
        currentTab={activeTab}
        onSelectTab={onSelectTab}
      />

      {/* Main Content Container - dynamically adjusts padding for desktop/tablet/mobile */}
      <div
        className={cn(
          "flex min-w-0 flex-col transition-[padding] duration-300 ease-in-out",
          isCollapsed ? "md:pl-[64px]" : "md:pl-[240px]"
        )}
      >
        {/* Navigation & Header Bar with Hamburger Toggle Button */}
        <div className="sticky top-0 z-20 flex items-center bg-[#101318]/90 backdrop-blur-md border-b border-[#1A1D23]">
          {/* Hamburger toggle for mobile & desktop */}
          <div className="flex items-center pl-3 pr-1 md:hidden">
            <SidebarToggle />
          </div>

          <div className="min-w-0 flex-1">
            <DashboardTopBar
              portfolioName={portfolioName}
              portfolioId={portfolioId}
              activeTab={activeTab as any}
              dataStatus={dataStatus}
              loading={loading}
              walletAddress={walletAddress}
              onNewPortfolio={onNewPortfolio}
              onOpenWallet={onOpenWallet}
              onOpenBuilder={onOpenBuilder}
              onOpenAttest={onOpenAttest}
              onOpenShare={onOpenShare}
              onApplyPreset={onApplyPreset}
            />
          </div>
        </div>

        {/* Scrollable Workstation Canvas */}
        <main
          id="dashboard-content"
          className="min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-8"
        >
          <div className="mx-auto w-full max-w-[1400px] space-y-6">
            {error && (
              <div
                role="alert"
                className="flex items-start justify-between gap-4 rounded-lg border border-[#D46B6B]/40 bg-[#D46B6B]/10 px-4 py-3"
              >
                <div className="min-w-0">
                  <p className="font-mono text-xs font-semibold text-[#D46B6B]">
                    ENGINE CALCULATION WARNING
                  </p>
                  <p className="mt-1 text-xs text-[#F4F2ED]">{error}</p>
                </div>
                <button
                  type="button"
                  onClick={onDismissError}
                  aria-label="Dismiss status message"
                  className="rounded p-1 text-[#9299A3] hover:text-[#F4F2ED]"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            )}

            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

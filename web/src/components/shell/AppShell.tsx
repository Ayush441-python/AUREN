"use client";

import React, { useState } from "react";
import { AurenSidebar } from "@/components/navigation/AurenSidebar";
import { SidebarToggle } from "@/components/navigation/SidebarToggle";
import { TopBar } from "./TopBar";
import { NavigationProvider, useNavigation } from "@/lib/navigationContext";
import type { NavItemKey } from "@/lib/navigationTypes";
import { cn } from "@/lib/cn";

export type NavTab = NavItemKey | string;

interface AppShellProps {
  children?: React.ReactNode;
  activeTab?: NavTab;
  onSelectTab?: (tab: any) => void;
  portfolioName?: string;
  onNewPortfolio?: () => void;
  onOpenWalletModal?: () => void;
  walletAddress?: string | null;
}

function ShellInner({
  children,
  activeTab = "overview",
  onSelectTab,
  portfolioName = "Sample: Balanced Multi-Asset",
  onNewPortfolio,
  onOpenWalletModal,
  walletAddress,
}: AppShellProps) {
  const { isCollapsed } = useNavigation();
  const [internalTab, setInternalTab] = useState<NavTab>(activeTab);
  const currentTab = onSelectTab ? activeTab : internalTab;
  const handleSelectTab = onSelectTab || setInternalTab;

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#0A0C0E] text-[#F4F2ED]">
      {/* Desktop & Tablet Sidebar */}
      <AurenSidebar
        currentTab={currentTab as NavItemKey}
        onSelectTab={handleSelectTab}
      />

      {/* Main Content Area */}
      <div
        className={cn(
          "flex flex-1 flex-col overflow-hidden transition-[padding] duration-300 ease-in-out",
          isCollapsed ? "md:pl-[64px]" : "md:pl-[240px]"
        )}
      >
        {/* TopBar with Hamburger Toggle for mobile */}
        <div className="flex items-center border-b border-[#1A1D23] bg-[#101318]/90 backdrop-blur-md">
          <div className="flex items-center pl-3 md:hidden">
            <SidebarToggle />
          </div>
          <div className="flex-1">
            <TopBar
              portfolioName={portfolioName}
              onNewPortfolio={onNewPortfolio}
              onOpenWalletModal={onOpenWalletModal}
              walletAddress={walletAddress}
              activeTab={currentTab as any}
            />
          </div>
        </div>

        {/* Scrollable Workstation Canvas */}
        <main className="flex-1 overflow-y-auto px-4 py-6 pb-20 md:px-8 md:pb-8 lg:px-10">
          <div className="mx-auto max-w-7xl">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

export function AppShell(props: AppShellProps) {
  return (
    <NavigationProvider defaultActive={(props.activeTab as NavItemKey) || "overview"}>
      <ShellInner {...props} />
    </NavigationProvider>
  );
}

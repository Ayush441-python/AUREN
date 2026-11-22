"use client";

import React, { useState } from "react";
import { Sidebar, NavTab } from "./Sidebar";
import { TopBar } from "./TopBar";
import { BottomTabs } from "./BottomTabs";

interface AppShellProps {
  children?: React.ReactNode;
  activeTab?: NavTab;
  onSelectTab?: (tab: NavTab) => void;
  portfolioName?: string;
  onNewPortfolio?: () => void;
  onOpenWalletModal?: () => void;
  walletAddress?: string | null;
}

export function AppShell({
  children,
  activeTab = "overview",
  onSelectTab,
  portfolioName = "Sample: Balanced Multi-Asset",
  onNewPortfolio,
  onOpenWalletModal,
  walletAddress,
}: AppShellProps) {
  const [internalTab, setInternalTab] = useState<NavTab>(activeTab);
  const currentTab = onSelectTab ? activeTab : internalTab;
  const handleSelectTab = onSelectTab || setInternalTab;

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#0E0E10] text-[#F5F6F7]">
      {/* Desktop & Tablet Sidebar */}
      <Sidebar activeTab={currentTab} onSelectTab={handleSelectTab} />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Persistent TopBar with Institutional Disclaimer */}
        <TopBar
          portfolioName={portfolioName}
          onNewPortfolio={onNewPortfolio}
          onOpenWalletModal={onOpenWalletModal}
          walletAddress={walletAddress}
          activeTab={currentTab}
        />

        {/* Scrollable Workstation Canvas */}
        <main className="flex-1 overflow-y-auto px-4 py-6 pb-20 md:px-8 md:pb-8 lg:px-10">
          <div className="mx-auto max-w-7xl">
            {children}
          </div>
        </main>
      </div>

      {/* Mobile Bottom Navigation Bar */}
      <BottomTabs activeTab={currentTab} onSelectTab={handleSelectTab} />
    </div>
  );
}

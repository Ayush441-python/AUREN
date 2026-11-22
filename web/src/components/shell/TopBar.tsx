"use client";

import React, { useState } from "react";
import { ChevronDown, ShieldAlert, Sparkles, Plus, Wallet, ExternalLink, Check } from "lucide-react";

interface TopBarProps {
  portfolioName?: string;
  onNewPortfolio?: () => void;
  onOpenWalletModal?: () => void;
  walletAddress?: string | null;
  activeTab?: string;
}

export function TopBar({
  portfolioName = "Sample: Balanced Multi-Asset",
  onNewPortfolio,
  onOpenWalletModal,
  walletAddress,
}: TopBarProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 flex h-14 w-full items-center justify-between border-b border-[#26262C] bg-[#151518]/95 px-4 md:px-6 backdrop-blur-sm">
      {/* Left: Portfolio Switcher & Identifier */}
      <div className="flex items-center gap-3">
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 rounded-md border border-[#26262C] bg-[#1C1C21] px-3 py-1.5 text-xs font-medium text-[#F5F6F7] transition hover:border-[#383842] hover:bg-[#23232A]"
            aria-label="Select portfolio"
          >
            <span className="h-2 w-2 rounded-full bg-[#E3B341]" />
            <span className="max-w-[140px] truncate sm:max-w-[220px] md:max-w-[320px]">
              {portfolioName}
            </span>
            <ChevronDown className="h-3.5 w-3.5 text-[#A1A4AB]" />
          </button>

          {dropdownOpen && (
            <div className="absolute left-0 mt-1.5 w-64 rounded-lg border border-[#26262C] bg-[#1C1C21] p-1.5 shadow-2xl z-50">
              <div className="px-2.5 py-1 text-[11px] font-medium uppercase tracking-wider text-[#6B6E76]">
                Institutional Workspaces
              </div>
              <button
                onClick={() => setDropdownOpen(false)}
                className="flex w-full items-center justify-between rounded-md px-2.5 py-1.5 text-xs text-[#F5F6F7] hover:bg-[#26262C]"
              >
                <span>Balanced Multi-Asset</span>
                <span className="font-mono text-[11px] text-[#A1A4AB]">5 assets</span>
              </button>
              <button
                onClick={() => setDropdownOpen(false)}
                className="flex w-full items-center justify-between rounded-md px-2.5 py-1.5 text-xs text-[#A1A4AB] hover:bg-[#26262C] hover:text-[#F5F6F7]"
              >
                <span>Mega-Cap Tech Focus</span>
                <span className="font-mono text-[11px] text-[#6B6E76]">4 assets</span>
              </button>
              <button
                onClick={() => setDropdownOpen(false)}
                className="flex w-full items-center justify-between rounded-md px-2.5 py-1.5 text-xs text-[#A1A4AB] hover:bg-[#26262C] hover:text-[#F5F6F7]"
              >
                <span>Digital Asset Core</span>
                <span className="font-mono text-[11px] text-[#6B6E76]">Crypto L1s</span>
              </button>

              <div className="my-1 border-t border-[#26262C]" />

              <button
                onClick={() => {
                  setDropdownOpen(false);
                  if (onNewPortfolio) onNewPortfolio();
                }}
                className="flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-xs font-medium text-[#E3B341] hover:bg-[#E3B341]/10"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>New Portfolio Model</span>
              </button>
            </div>
          )}
        </div>

        {/* Live Base RPC Telemetry */}
        <div className="hidden lg:flex items-center gap-1.5 rounded-full border border-[#26262C] bg-[#0E0E10] px-2.5 py-1 text-[11px] text-[#A1A4AB]">
          <span className="h-1.5 w-1.5 rounded-full bg-[#7FB3A6]" />
          <span className="font-mono text-[10px] uppercase tracking-wide text-[#7FB3A6]">Base RPC 4-Node Pool</span>
        </div>
      </div>

      {/* Center: Mandatory Institutional Disclaimer Pill */}
      <div className="flex items-center">
        <div className="flex items-center gap-1.5 rounded-full border border-[#26262C] bg-[#1C1C21] px-3 py-1 text-[11px] font-medium text-[#A1A4AB] shadow-sm">
          <ShieldAlert className="h-3 w-3 text-[#A1A4AB]" />
          <span>Analytics only, not investment advice</span>
        </div>
      </div>

      {/* Right: Wallet Connect & New Portfolio */}
      <div className="flex items-center gap-2">
        {onOpenWalletModal && (
          walletAddress ? (
            <button
              onClick={onOpenWalletModal}
              className="flex items-center gap-2 rounded-md border border-[#7FB3A6]/30 bg-[#7FB3A6]/10 px-3 py-1.5 text-xs font-mono font-medium text-[#7FB3A6] transition hover:bg-[#7FB3A6]/20"
              title="Connected Base Wallet"
            >
              <span className="h-2 w-2 rounded-full bg-[#7FB3A6] animate-pulse" />
              <span>
                {walletAddress.slice(0, 6)}...{walletAddress.slice(-4)}
              </span>
            </button>
          ) : (
            <button
              onClick={onOpenWalletModal}
              className="flex items-center gap-1.5 rounded-md border border-[#26262C] bg-[#1C1C21] px-3 py-1.5 text-xs font-medium text-[#F5F6F7] transition hover:border-[#383842] hover:bg-[#23232A]"
            >
              <Wallet className="h-3.5 w-3.5 text-[#E3B341]" />
              <span className="hidden sm:inline">Connect Wallet</span>
              <span className="sm:hidden">Wallet</span>
            </button>
          )
        )}

        <button
          onClick={onNewPortfolio}
          className="flex items-center gap-1.5 rounded-md bg-[#E3B341] px-3 py-1.5 text-xs font-semibold text-[#0E0E10] transition hover:bg-[#f0c254] active:scale-[0.98]"
        >
          <Plus className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">New Portfolio</span>
          <span className="sm:hidden">New</span>
        </button>
      </div>
    </header>
  );
}

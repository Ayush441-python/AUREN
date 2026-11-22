"use client";

import React from "react";
import {
  LayoutDashboard,
  PieChart,
  Grid3X3,
  Activity,
  FileText,
  ShieldCheck,
  ExternalLink,
  Sliders,
} from "lucide-react";

export type NavTab = "overview" | "exposure" | "correlation" | "stress" | "report" | "docs";

interface SidebarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
}

export function Sidebar({ activeTab, onSelectTab }: SidebarProps) {
  const navItems: { id: NavTab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: "overview", label: "Risk Overview", icon: LayoutDashboard },
    { id: "exposure", label: "Exposure & Factor", icon: PieChart },
    { id: "correlation", label: "Correlation Matrix", icon: Grid3X3 },
    { id: "stress", label: "Stress & Sandbox", icon: Activity },
    { id: "report", label: "AI Verification", icon: FileText },
    { id: "docs", label: "Proof & API Docs", icon: ShieldCheck },
  ];

  return (
    <aside className="hidden md:flex h-screen flex-col justify-between border-r border-[#26262C] bg-[#151518] md:w-16 lg:w-[220px] transition-all duration-200 select-none">
      {/* Brand Header */}
      <div>
        <div className="flex h-14 items-center border-b border-[#26262C] px-4 lg:px-5">
          <div className="flex items-center gap-2.5">
            {/* Gold Ring Monogram */}
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[#1C1C21] border border-[#26262C]">
              <span className="text-sm font-bold text-[#E3B341]">◐</span>
            </div>
            <div className="hidden lg:flex flex-col">
              <span className="text-sm font-semibold tracking-wider text-[#F5F6F7]">
                AUREN
              </span>
              <span className="font-mono text-[9px] uppercase tracking-widest text-[#6B6E76]">
                Risk Intelligence
              </span>
            </div>
          </div>
        </div>

        {/* Navigation Item List */}
        <nav className="p-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`group flex w-full items-center gap-3 rounded-md px-2.5 py-2 text-xs font-medium transition-colors ${
                  isActive
                    ? "bg-[#1C1C21] text-[#F5F6F7] shadow-sm relative before:absolute before:left-0 before:top-1.5 before:bottom-1.5 before:w-1 before:rounded-r before:bg-[#E3B341]"
                    : "text-[#A1A4AB] hover:bg-[#1C1C21]/60 hover:text-[#F5F6F7]"
                }`}
                title={item.label}
              >
                <Icon
                  className={`h-4 w-4 shrink-0 transition-colors ${
                    isActive ? "text-[#E3B341]" : "text-[#A1A4AB] group-hover:text-[#F5F6F7]"
                  }`}
                />
                <span className="hidden lg:inline truncate">{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer System Telemetry */}
      <div className="border-t border-[#26262C] p-3 lg:p-4">
        <div className="hidden lg:flex flex-col gap-1.5 rounded-md border border-[#26262C] bg-[#0E0E10] p-2.5">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-[#6B6E76]">Engine</span>
            <span className="font-mono font-medium text-[#7FB3A6]">v1.0.4 Online</span>
          </div>
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-[#6B6E76]">Model</span>
            <span className="font-mono text-[#A1A4AB]">Covariance 252d</span>
          </div>
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-[#6B6E76]">Network</span>
            <span className="font-mono text-[#A1A4AB]">Base Mainnet</span>
          </div>
        </div>

        {/* Tablet Monogram Status Dot */}
        <div className="flex lg:hidden justify-center py-2">
          <span className="h-2 w-2 rounded-full bg-[#7FB3A6]" title="Engine Online" />
        </div>
      </div>
    </aside>
  );
}

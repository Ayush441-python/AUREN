"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Compass,
  LayoutDashboard,
  Briefcase,
  ShieldAlert,
  Globe,
  Gauge,
  PieChart,
  GitFork,
  Activity,
  History,
  Flame,
  Bookmark,
  FolderLock,
  FileCheck2,
  Sliders,
  BookOpen,
  HelpCircle,
  PanelLeftClose,
  PanelLeftOpen,
  X,
  ExternalLink,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/cn";
import { useNavigation } from "@/lib/navigationContext";
import type { NavItemKey, NavSectionKey } from "@/lib/navigationTypes";

interface NavEntry {
  id: NavItemKey;
  label: string;
  icon: React.ComponentType<{ className?: string; "aria-hidden"?: boolean }>;
  route: string;
  badge?: string;
  description?: string;
}

interface NavSection {
  key: NavSectionKey;
  title: string;
  items: NavEntry[];
}

export const NAVIGATION_STRUCTURE: NavSection[] = [
  {
    key: "MAIN",
    title: "MAIN",
    items: [
      {
        id: "overview",
        label: "Overview",
        icon: Compass,
        route: "/dashboard?tab=overview",
        description: "Portfolio executive summary and risk composite",
      },
      {
        id: "dashboard",
        label: "Dashboard",
        icon: LayoutDashboard,
        route: "/dashboard",
        description: "Primary analytics workstation and KPIs",
      },
      {
        id: "portfolio",
        label: "Portfolio",
        icon: Briefcase,
        route: "/dashboard?tab=portfolio",
        description: "Holdings allocation and exposure breakdown",
      },
      {
        id: "risk-analysis",
        label: "Risk Analysis",
        icon: ShieldAlert,
        route: "/dashboard?tab=risk-analysis",
        description: "VaR, CVaR and downside tail distribution",
      },
      {
        id: "market-overview",
        label: "Market Overview",
        icon: Globe,
        route: "/dashboard?tab=market-overview",
        description: "Cross-asset macroeconomic backdrop and indexes",
      },
    ],
  },
  {
    key: "ANALYTICS",
    title: "ANALYTICS",
    items: [
      {
        id: "risk-metrics",
        label: "Risk Metrics",
        icon: Gauge,
        route: "/dashboard?tab=risk-metrics",
        description: "Parametric Sharpe, Sortino, and Beta coefficients",
      },
      {
        id: "asset-allocation",
        label: "Asset Allocation",
        icon: PieChart,
        route: "/dashboard?tab=asset-allocation",
        description: "Sector weightings, asset classes and factors",
      },
      {
        id: "correlation-analysis",
        label: "Correlation Analysis",
        icon: GitFork,
        route: "/dashboard?tab=correlation-analysis",
        description: "Empirical asset cross-correlation matrix",
      },
      {
        id: "volatility",
        label: "Volatility",
        icon: Activity,
        route: "/dashboard?tab=volatility",
        description: "Rolling realized volatility and EWMA surface",
      },
      {
        id: "historical-performance",
        label: "Historical Performance",
        icon: History,
        route: "/dashboard?tab=historical-performance",
        description: "Multi-year drawdown cycles and benchmark alpha",
      },
      {
        id: "stress-testing",
        label: "Stress Testing",
        icon: Flame,
        route: "/dashboard?tab=stress-testing",
        description: "Macro shock simulations and custom sandbox",
      },
    ],
  },
  {
    key: "WORKSPACE",
    title: "WORKSPACE",
    items: [
      {
        id: "watchlist",
        label: "Watchlist",
        icon: Bookmark,
        route: "/dashboard?tab=watchlist",
        description: "Tracked tickers, instruments, and alerts",
      },
      {
        id: "saved-portfolios",
        label: "Saved Portfolios",
        icon: FolderLock,
        route: "/dashboard?tab=saved-portfolios",
        description: "Versioned portfolio profiles and snapshots",
      },
      {
        id: "reports",
        label: "Reports",
        icon: FileCheck2,
        route: "/dashboard?tab=reports",
        description: "Deterministic audit reports and formal decks",
      },
    ],
  },
  {
    key: "PREFERENCES",
    title: "PREFERENCES",
    items: [
      {
        id: "settings",
        label: "Settings",
        icon: Sliders,
        route: "/dashboard?tab=settings",
        description: "Engine calculation parameters and display units",
      },
      {
        id: "docs",
        label: "API & Proof",
        icon: BookOpen,
        route: "/dashboard?tab=docs",
        description: "Endpoint documentation, request examples, and proof rules",
      },
      {
        id: "help-support",
        label: "Help & Support",
        icon: HelpCircle,
        route: "/dashboard?tab=help-support",
        description: "Mathematical formulation docs and platform guide",
      },
    ],
  },
];

interface AurenSidebarProps {
  currentTab?: string;
  onSelectTab?: (tab: NavItemKey) => void;
  className?: string;
}

export function AurenSidebar({
  currentTab,
  onSelectTab,
  className,
}: AurenSidebarProps) {
  const {
    isCollapsed,
    toggleCollapsed,
    isMobileOpen,
    setIsMobileOpen,
    activeItem,
    setActiveItem,
  } = useNavigation();

  const router = useRouter();
  const [hoveredItem, setHoveredItem] = useState<NavItemKey | null>(null);

  // Synchronize internal active state with prop if given
  const currentActive = (currentTab as NavItemKey) || activeItem;

  const handleItemClick = (entry: NavEntry, e: React.MouseEvent) => {
    e.preventDefault();
    setActiveItem(entry.id);
    if (onSelectTab) {
      onSelectTab(entry.id);
    } else {
      router.push(entry.route);
    }
    // Dismiss mobile drawer on navigation
    if (isMobileOpen) {
      setIsMobileOpen(false);
    }
  };

  const renderContent = (isDrawer = false) => {
    const collapsed = isDrawer ? false : isCollapsed;

    return (
      <div className="flex h-full flex-col justify-between overflow-hidden bg-[#0A0C0E] text-[#E4E6EA]">
        {/* Top Header & Brand Monogram */}
        <div className="shrink-0">
          <div
            className={cn(
              "flex h-16 items-center border-b border-[#1A1D23] px-3.5 transition-all duration-300",
              collapsed ? "justify-center px-2" : "justify-between"
            )}
          >
            {/* AUREN Emblem */}
            <Link
              href="/"
              className="group flex items-center gap-3 outline-none"
              title="AUREN Risk Intelligence"
            >
              {/* Precision FinTech Monogram */}
              <div className="relative flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-[#272B33] bg-[#12151B] transition-colors duration-200 group-hover:border-[#D6B56D]/60 group-hover:bg-[#161A22]">
                {/* Geometric gold chevron/diamond emblem */}
                <svg
                  viewBox="0 0 24 24"
                  className="h-4 w-4 text-[#D6B56D] transition-transform duration-300 group-hover:scale-105"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                >
                  <polygon points="12 3 20 8.5 20 15.5 12 21 4 15.5 4 8.5" />
                  <line x1="12" y1="3" x2="12" y2="21" strokeDasharray="2 2" strokeOpacity="0.6" />
                  <circle cx="12" cy="12" r="2.5" fill="#D6B56D" stroke="none" />
                </svg>
              </div>

              {!collapsed && (
                <div className="flex flex-col overflow-hidden text-left">
                  <div className="flex items-center gap-1.5">
                    <span className="font-sans text-[13px] font-bold tracking-[0.22em] text-[#F4F2ED] uppercase">
                      AUREN
                    </span>
                    <span className="rounded bg-[#D6B56D]/15 px-1 py-0.2 font-mono text-[8px] font-semibold tracking-wider text-[#D6B56D]">
                      PRO
                    </span>
                  </div>
                  <span className="font-mono text-[9px] uppercase tracking-widest text-[#636B75]">
                    Risk Intelligence
                  </span>
                </div>
              )}
            </Link>

            {/* Desktop Collapse / Mobile Dismiss Button */}
            {isDrawer ? (
              <button
                type="button"
                onClick={() => setIsMobileOpen(false)}
                className="rounded-md border border-[#272B33] p-1.5 text-[#9299A3] transition-colors hover:border-[#D6B56D]/40 hover:bg-[#161A22] hover:text-[#F4F2ED]"
                aria-label="Close navigation drawer"
              >
                <X className="h-4 w-4" />
              </button>
            ) : (
              !collapsed && (
                <button
                  type="button"
                  onClick={toggleCollapsed}
                  className="rounded-md border border-[#272B33] p-1.5 text-[#9299A3] transition-colors hover:border-[#D6B56D]/40 hover:bg-[#161A22] hover:text-[#F4F2ED]"
                  aria-label="Collapse sidebar"
                  title="Collapse sidebar (Ctrl+B)"
                >
                  <PanelLeftClose className="h-3.5 w-3.5" />
                </button>
              )
            )}
          </div>
        </div>

        {/* Scrollable Navigation Body */}
        <div className="flex-1 overflow-y-auto px-2 py-3.5 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-[#1D2128]">
          <div className="space-y-6">
            {NAVIGATION_STRUCTURE.map((section) => (
              <div key={section.key} className="space-y-1">
                {/* Section Header */}
                {!collapsed ? (
                  <div className="px-2.5 pb-1.5 pt-1">
                    <span className="font-mono text-[9px] font-semibold uppercase tracking-[0.2em] text-[#636B75]">
                      {section.title}
                    </span>
                  </div>
                ) : (
                  <div className="my-1.5 flex justify-center">
                    <span className="h-[1px] w-5 bg-[#1F232B]" />
                  </div>
                )}

                {/* Section Items */}
                <div className="space-y-0.5">
                  {section.items.map((item) => {
                    const Icon = item.icon;
                    const isActive = currentActive === item.id;
                    const isHovered = hoveredItem === item.id;

                    return (
                      <div
                        key={item.id}
                        className="relative"
                        onMouseEnter={() => setHoveredItem(item.id)}
                        onMouseLeave={() => setHoveredItem(null)}
                      >
                        <a
                          href={item.route}
                          onClick={(e) => handleItemClick(item, e)}
                          className={cn(
                            "group relative flex items-center gap-3 rounded-md px-2.5 py-2 text-xs font-medium transition-all duration-150 outline-none",
                            collapsed ? "justify-center px-0 w-10 h-10 mx-auto" : "w-full",
                            isActive
                              ? "bg-[#14171E] text-[#F4F2ED] font-semibold border border-[#2A2E38]"
                              : "text-[#9299A3] hover:bg-[#13161C] hover:text-[#F4F2ED] border border-transparent"
                          )}
                          aria-current={isActive ? "page" : undefined}
                          title={!collapsed ? undefined : item.label}
                        >
                          {/* Active Gold Indicator Pillar */}
                          {isActive && (
                            <span
                              className={cn(
                                "absolute rounded bg-[#D6B56D] shadow-[0_0_8px_rgba(214,181,109,0.35)]",
                                collapsed
                                  ? "left-0 top-2 bottom-2 w-[2.5px] rounded-r"
                                  : "left-0 top-1.5 bottom-1.5 w-[2.5px] rounded-r"
                              )}
                              aria-hidden="true"
                            />
                          )}

                          {/* Navigation Icon */}
                          <Icon
                            aria-hidden={true}
                            className={cn(
                              "h-4 w-4 shrink-0 transition-colors duration-150",
                              isActive
                                ? "text-[#D6B56D]"
                                : "text-[#7B828E] group-hover:text-[#D6B56D]/80"
                            )}
                          />

                          {/* Nav Item Label */}
                          {!collapsed && (
                            <div className="flex flex-1 items-center justify-between overflow-hidden">
                              <span className="truncate tracking-wide text-[12px]">
                                {item.label}
                              </span>
                              {isActive && (
                                <ChevronRight className="h-3 w-3 text-[#D6B56D]/60" />
                              )}
                            </div>
                          )}
                        </a>

                        {/* Collapsed Mode Floating Tooltip */}
                        {collapsed && isHovered && (
                          <div
                            role="tooltip"
                            className="pointer-events-none fixed z-50 ml-3 flex -translate-y-1/2 flex-col rounded-md border border-[#272B33] bg-[#14171E] px-3 py-1.5 shadow-2xl backdrop-blur-md"
                            style={{
                              left: "68px",
                              transform: "translateY(-50%)",
                            }}
                          >
                            <div className="flex items-center gap-2">
                              <span className="font-sans text-xs font-semibold text-[#F4F2ED]">
                                {item.label}
                              </span>
                              <span className="font-mono text-[9px] uppercase tracking-wider text-[#636B75]">
                                {section.title}
                              </span>
                            </div>
                            {item.description && (
                              <span className="mt-0.5 max-w-[200px] text-[10px] leading-tight text-[#9299A3]">
                                {item.description}
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom Section: Engine Status & Toggle Action */}
        <div className="shrink-0 border-t border-[#1A1D23] p-2.5">
          {!collapsed ? (
            <div className="space-y-2">
              {/* Telemetry Indicator */}
              <div className="flex items-center justify-between rounded-md border border-[#1F232B] bg-[#101318] px-2.5 py-2">
                <div className="flex items-center gap-2">
                  <span className="relative flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#36A879] opacity-75" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-[#36A879]" />
                  </span>
                  <div className="flex flex-col">
                    <span className="font-mono text-[9px] font-semibold uppercase tracking-wider text-[#9299A3]">
                      Risk Engine
                    </span>
                    <span className="font-mono text-[10px] text-[#F4F2ED]">
                      v1.4.2 · Deterministic
                    </span>
                  </div>
                </div>
                <div className="rounded border border-[#272B33] bg-[#161A22] px-1.5 py-0.5 font-mono text-[9px] font-medium text-[#D6B56D]">
                  252d
                </div>
              </div>

              {/* Quick Collapsed Trigger */}
              <button
                type="button"
                onClick={toggleCollapsed}
                className="flex w-full items-center justify-center gap-2 rounded-md border border-[#1F232B] px-2.5 py-1.5 text-[11px] font-medium text-[#9299A3] transition-colors hover:border-[#D6B56D]/40 hover:bg-[#13161C] hover:text-[#F4F2ED]"
              >
                <PanelLeftClose className="h-3.5 w-3.5" />
                <span>Collapse Navigation</span>
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 py-1">
              {/* Collapsed Expand Trigger */}
              <button
                type="button"
                onClick={toggleCollapsed}
                className="flex h-9 w-9 items-center justify-center rounded-md border border-[#1F232B] bg-[#101318] text-[#9299A3] transition-colors hover:border-[#D6B56D]/40 hover:text-[#D6B56D]"
                aria-label="Expand sidebar"
                title="Expand navigation"
              >
                <PanelLeftOpen className="h-4 w-4" />
              </button>

              {/* Status Dot */}
              <span
                className="h-2 w-2 rounded-full bg-[#36A879]"
                title="Risk Engine Online (252d)"
              />
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <>
      {/* Desktop & Tablet Sidebar (Fixed, non-scrolling while content scrolls) */}
      <aside
        aria-label="AUREN navigation sidebar"
        className={cn(
          "fixed inset-y-0 left-0 z-30 hidden border-r border-[#1A1D23] md:block transition-[width] duration-300 ease-in-out select-none",
          isCollapsed ? "w-[64px]" : "w-[240px]",
          className
        )}
      >
        {renderContent(false)}
      </aside>

      {/* Mobile Off-Canvas Drawer Backdrop */}
      {isMobileOpen && (
        <div
          role="presentation"
          onClick={() => setIsMobileOpen(false)}
          className="fixed inset-0 z-40 bg-black/75 backdrop-blur-xs transition-opacity duration-300 md:hidden animate-in fade-in"
        />
      )}

      {/* Mobile Off-Canvas Drawer */}
      <aside
        aria-label="Mobile navigation drawer"
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-[280px] border-r border-[#1A1D23] shadow-2xl transition-transform duration-300 ease-in-out md:hidden select-none",
          isMobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {renderContent(true)}
      </aside>
    </>
  );
}

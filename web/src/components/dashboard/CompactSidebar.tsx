"use client";

import {
  Activity,
  ArrowUpRight,
  ChevronsLeft,
  ChevronsRight,
  FileText,
  Grid3X3,
  LayoutDashboard,
  PieChart,
  ShieldCheck,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/cn";
import type { DataStatus, DashboardTab } from "@/components/dashboard/Workstation";

interface CompactSidebarProps {
  activeTab: DashboardTab;
  onSelectTab: (tab: DashboardTab) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  portfolioLabel: string;
  dataStatus: DataStatus;
}

const navItems: {
  id: DashboardTab;
  label: string;
  code: string;
  icon: typeof LayoutDashboard;
}[] = [
  { id: "overview", label: "Risk Overview", code: "01", icon: LayoutDashboard },
  { id: "exposure", label: "Exposure & Factor", code: "02", icon: PieChart },
  { id: "correlation", label: "Correlation Matrix", code: "03", icon: Grid3X3 },
  { id: "stress", label: "Stress & Sandbox", code: "04", icon: Activity },
  { id: "report", label: "AI Verification", code: "05", icon: FileText },
  { id: "docs", label: "Proof & API Docs", code: "06", icon: ShieldCheck },
];

const statusCopy: Record<DataStatus, string> = {
  reference: "Reference data",
  live: "Live analysis",
  stale: "Previous data",
};

export function CompactSidebar({
  activeTab,
  onSelectTab,
  collapsed,
  onToggleCollapse,
  portfolioLabel,
  dataStatus,
}: CompactSidebarProps) {
  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-40 hidden flex-col border-r border-line bg-secondary/95 backdrop-blur-sm lg:flex",
        collapsed ? "w-[72px]" : "w-[72px] xl:w-[244px]"
      )}
    >
      <div className="flex h-16 shrink-0 items-center justify-center border-b border-line px-3 xl:justify-between xl:px-5">
        <span className="inline-flex min-w-0 items-center gap-2.5">
          <svg
            aria-hidden="true"
            viewBox="0 0 24 24"
            className="h-4 w-4 shrink-0 text-gold"
            fill="none"
          >
            <path d="M12 1.5 22.5 12 12 22.5 1.5 12 12 1.5Z" stroke="currentColor" strokeWidth="0.8" />
            <path d="M12 6.4 17.6 12 12 17.6 6.4 12 12 6.4Z" fill="currentColor" />
            <path d="M12 9.2 14.8 12 12 14.8 9.2 12 12 9.2Z" fill="#080808" />
          </svg>
          <span
            className={cn(
              "hidden min-w-0 font-display text-lg uppercase leading-none tracking-[0.3em] text-primary xl:block",
              collapsed && "xl:hidden"
            )}
          >
            Auren
          </span>
        </span>
        <button
          type="button"
          onClick={onToggleCollapse}
          aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}
          aria-expanded={!collapsed}
          className={cn(
            "hidden border border-line p-1.5 text-muted transition-colors hover:border-gold/50 hover:text-highlight xl:inline-flex",
            !collapsed && "xl:inline-flex"
          )}
        >
          {collapsed ? (
            <ChevronsRight className="h-3.5 w-3.5" aria-hidden="true" />
          ) : (
            <ChevronsLeft className="h-3.5 w-3.5" aria-hidden="true" />
          )}
        </button>
      </div>

      <nav aria-label="Workstation sections" className="min-h-0 flex-1 overflow-y-auto p-2 xl:p-3">
        <p
          className={cn(
            "auren-eyebrow mb-3 px-2 text-center xl:text-left",
            collapsed && "xl:text-center"
          )}
        >
          <span className="xl:hidden">Sections</span>
          <span className="hidden xl:inline">Analysis sections</span>
        </p>
        <ul className="space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = activeTab === item.id;
            return (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={() => onSelectTab(item.id)}
                  aria-current={active ? "page" : undefined}
                  title={item.label}
                  className={cn(
                    "group relative flex w-full items-center justify-center gap-3 border border-transparent px-2 py-3 text-left transition-colors xl:justify-start xl:px-3",
                    active
                      ? "border-gold/25 bg-gold/[0.08] text-highlight"
                      : "text-muted hover:border-line hover:bg-elevated/60 hover:text-primary"
                  )}
                >
                  <Icon
                    aria-hidden="true"
                    className={cn("h-4 w-4 shrink-0", active ? "text-gold" : "text-faint group-hover:text-champagne")}
                  />
                  <span
                    className={cn(
                      "hidden min-w-0 flex-1 xl:block",
                      collapsed && "xl:hidden"
                    )}
                  >
                    <span className="block truncate text-[0.7rem] uppercase tracking-[0.12em]">
                      {item.label}
                    </span>
                  </span>
                  <span
                    className={cn(
                      "hidden font-mono text-[0.58rem] tracking-[0.12em] xl:block",
                      collapsed && "xl:hidden",
                      active ? "text-gold" : "text-faint"
                    )}
                  >
                    {item.code}
                  </span>
                  {active && (
                    <span
                      aria-hidden="true"
                      className="absolute inset-y-2 left-0 w-[2px] bg-gold xl:left-auto xl:right-0"
                    />
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="shrink-0 border-t border-line p-2 xl:p-4">
        <div
          className={cn(
            "mb-3 border border-line bg-obsidian/70 px-3 py-3",
            collapsed && "xl:hidden"
          )}
        >
          <p className="font-mono text-[0.58rem] uppercase tracking-[0.18em] text-faint">
            Portfolio context
          </p>
          <p className="mt-1.5 truncate text-xs text-primary" title={portfolioLabel}>
            {portfolioLabel}
          </p>
          <p className="mt-2 font-mono text-[0.6rem] uppercase tracking-[0.14em] text-champagne">
            {statusCopy[dataStatus]}
          </p>
        </div>
        <div className={cn("mb-3 flex justify-center py-1", collapsed && "xl:hidden")}>
          <span className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-muted">
            {statusCopy[dataStatus]}
          </span>
        </div>
        <Link
          href="/"
          title="Return to site"
          className="flex items-center justify-center gap-2 border border-line px-2 py-2.5 text-[0.62rem] uppercase tracking-[0.16em] text-muted transition-colors hover:border-gold/50 hover:text-highlight xl:justify-start xl:px-3"
        >
          <ArrowUpRight aria-hidden="true" className="h-3.5 w-3.5 shrink-0 text-gold" />
          <span className={cn("hidden xl:inline", collapsed && "xl:hidden")}>Return to site</span>
        </Link>
      </div>
    </aside>
  );
}

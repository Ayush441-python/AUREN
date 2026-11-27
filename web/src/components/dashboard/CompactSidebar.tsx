"use client";

import {
  Activity,
  ArrowUpRight,
  ChevronsLeft,
  ChevronsRight,
  FileText,
  Grid3X3,
  LayoutDashboard,
  type LucideIcon,
  PieChart,
  Presentation,
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

interface NavItem {
  id: DashboardTab;
  label: string;
  icon: LucideIcon;
}

const NAV_ITEMS: readonly NavItem[] = [
  { id: "overview", label: "Risk Overview", icon: LayoutDashboard },
  { id: "asset-allocation", label: "Factor Exposure", icon: PieChart },
  { id: "correlation-analysis", label: "Correlation Matrix", icon: Grid3X3 },
  { id: "stress-testing", label: "Stress Testing", icon: Activity },
  { id: "reports", label: "AI Verification", icon: FileText },
  { id: "historical-performance", label: "Executive Deck", icon: Presentation },
  { id: "docs", label: "API & Proof", icon: ShieldCheck },
];

const STATUS_LABEL: Record<DataStatus, string> = {
  reference: "Reference Dataset",
  live: "Live Engine Analysis",
  stale: "Previous Calculation",
};

export function CompactSidebar({
  activeTab,
  onSelectTab,
  collapsed,
  onToggleCollapse,
  portfolioLabel,
  dataStatus,
}: CompactSidebarProps) {
  const expandedOnly = collapsed ? "hidden" : "hidden xl:block";

  return (
    <aside
      aria-label="Workstation sidebar"
      className={cn(
        "fixed inset-y-0 left-0 z-40 hidden flex-col border-r border-line bg-secondary/95 backdrop-blur-sm lg:flex transition-[width] duration-200",
        collapsed ? "w-[68px]" : "w-[68px] xl:w-[240px]"
      )}
    >
      {/* Brand Header */}
      <div
        className={cn(
          "flex h-14 shrink-0 items-center justify-between border-b border-line px-3.5",
          collapsed && "justify-center px-2"
        )}
      >
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg border border-line bg-elevated text-gold shrink-0">
            <svg aria-hidden="true" viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <span
            className={cn(
              "font-sans font-bold uppercase tracking-[0.16em] text-primary text-sm",
              expandedOnly
            )}
          >
            Auren
          </span>
        </Link>

        <button
          type="button"
          onClick={onToggleCollapse}
          aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}
          className={cn(
            "hidden rounded-md border border-line p-1 text-muted transition-colors hover:border-gold/40 hover:text-primary xl:inline-flex",
            collapsed && "xl:hidden"
          )}
        >
          {collapsed ? <ChevronsRight className="h-3.5 w-3.5" /> : <ChevronsLeft className="h-3.5 w-3.5" />}
        </button>
      </div>

      {/* Navigation List */}
      <nav aria-label="Workstation Navigation" className="flex-1 overflow-y-auto p-2">
        <p className={cn("px-2.5 pt-2 pb-1.5 font-mono text-[0.62rem] font-semibold uppercase tracking-wider text-muted", expandedOnly)}>
          Analytics Modules
        </p>

        <ul className="space-y-1">
          {NAV_ITEMS.map((item, index) => {
            const Icon = item.icon;
            const active = activeTab === item.id;
            const code = String(index + 1).padStart(2, "0");

            return (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={() => onSelectTab(item.id)}
                  aria-current={active ? "page" : undefined}
                  title={item.label}
                  className={cn(
                    "group relative flex w-full items-center justify-center gap-3 rounded-lg border border-transparent px-2.5 py-2 text-left text-xs font-medium transition-colors",
                    !collapsed && "xl:justify-start xl:px-3",
                    active
                      ? "border-line bg-elevated text-primary font-semibold"
                      : "text-muted hover:border-line/60 hover:bg-elevated/40 hover:text-primary"
                  )}
                >
                  <Icon
                    aria-hidden="true"
                    className={cn(
                      "h-4 w-4 shrink-0 transition-colors",
                      active ? "text-gold" : "text-muted group-hover:text-primary"
                    )}
                  />
                  <span className={cn("truncate", expandedOnly)}>
                    {item.label}
                  </span>
                  <span
                    aria-hidden="true"
                    className={cn(
                      "ml-auto font-mono text-[0.62rem] text-muted",
                      expandedOnly,
                      active && "text-gold"
                    )}
                  >
                    {code}
                  </span>
                  {active && (
                    <span aria-hidden="true" className="absolute left-0 top-1.5 bottom-1.5 w-[2px] rounded-r bg-gold" />
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer Info / Portfolio Context */}
      <div className="shrink-0 border-t border-line p-3">
        <div className={cn("rounded-lg border border-line bg-elevated p-2.5", expandedOnly)}>
          <span className="font-mono text-[0.6rem] font-semibold uppercase tracking-wider text-muted">
            Active Context
          </span>
          <p className="mt-1 truncate text-xs font-semibold text-primary" title={portfolioLabel}>
            {portfolioLabel}
          </p>
          <div className="mt-2 flex items-center gap-1.5 text-[0.68rem] text-gold">
            <span className={cn(
              "h-1.5 w-1.5 rounded-full shrink-0",
              dataStatus === "live" ? "bg-positive" : "bg-gold"
            )} />
            <span className="truncate font-mono">{STATUS_LABEL[dataStatus]}</span>
          </div>
        </div>

        <Link
          href="/"
          className={cn(
            "mt-2 flex items-center justify-center gap-2 rounded-lg border border-line px-2 py-2 text-xs font-medium text-muted transition-colors hover:border-gold/40 hover:text-primary",
            !collapsed && "xl:justify-start xl:px-3"
          )}
          title="Exit to home"
        >
          <ArrowUpRight className="h-3.5 w-3.5 shrink-0 text-gold" />
          <span className={expandedOnly}>Return to Home</span>
        </Link>
      </div>
    </aside>
  );
}

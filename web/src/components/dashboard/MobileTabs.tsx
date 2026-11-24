"use client";

import {
  Activity,
  FileText,
  Grid3X3,
  LayoutDashboard,
  PieChart,
  ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/cn";
import type { DashboardTab } from "@/components/dashboard/Workstation";

interface MobileTabsProps {
  activeTab: DashboardTab;
  onSelectTab: (tab: DashboardTab) => void;
}

const tabs: { id: DashboardTab; label: string; icon: typeof LayoutDashboard }[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "exposure", label: "Exposure", icon: PieChart },
  { id: "correlation", label: "Matrix", icon: Grid3X3 },
  { id: "stress", label: "Stress", icon: Activity },
  { id: "report", label: "Report", icon: FileText },
  { id: "docs", label: "Docs", icon: ShieldCheck },
];

export function MobileTabs({ activeTab, onSelectTab }: MobileTabsProps) {
  return (
    <nav
      aria-label="Mobile workstation sections"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-obsidian/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-md lg:hidden"
    >
      <ul className="grid grid-cols-6">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <li key={tab.id} className="min-w-0">
              <button
                type="button"
                onClick={() => onSelectTab(tab.id)}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "relative flex h-14 w-full flex-col items-center justify-center gap-1 px-0.5 transition-colors",
                  active ? "text-highlight" : "text-faint"
                )}
              >
                {active && (
                  <span
                    aria-hidden="true"
                    className="absolute inset-x-2 top-0 h-[2px] bg-gold"
                  />
                )}
                <Icon
                  aria-hidden="true"
                  className={cn("h-4 w-4 shrink-0", active && "text-gold")}
                />
                <span className="w-full truncate text-center text-[0.56rem] uppercase tracking-[0.06em]">
                  {tab.label}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

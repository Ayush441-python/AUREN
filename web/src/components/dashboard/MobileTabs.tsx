"use client";

import {
  Compass,
  LayoutDashboard,
  ShieldAlert,
  Globe,
  Sliders,
} from "lucide-react";
import { cn } from "@/lib/cn";
import type { NavItemKey } from "@/lib/navigationTypes";

interface MobileTabsProps {
  activeTab: NavItemKey | string;
  onSelectTab: (tab: any) => void;
}

const tabs: { id: NavItemKey; label: string; icon: typeof Compass }[] = [
  { id: "overview", label: "Overview", icon: Compass },
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "risk-analysis", label: "Risk", icon: ShieldAlert },
  { id: "market-overview", label: "Market", icon: Globe },
  { id: "settings", label: "Settings", icon: Sliders },
];

export function MobileTabs({ activeTab, onSelectTab }: MobileTabsProps) {
  return (
    <nav
      aria-label="Mobile quick navigation"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-[#1A1D23] bg-[#0A0C0E]/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-md md:hidden"
    >
      <ul className="grid grid-cols-5">
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
                  active ? "text-[#D6B56D]" : "text-[#7B828E]"
                )}
              >
                {active && (
                  <span
                    aria-hidden="true"
                    className="absolute top-0 inset-x-3 h-0.5 rounded-full bg-[#D6B56D]"
                  />
                )}
                <Icon aria-hidden="true" className="h-4 w-4 shrink-0" />
                <span className="truncate text-[0.62rem] font-medium tracking-tight">
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

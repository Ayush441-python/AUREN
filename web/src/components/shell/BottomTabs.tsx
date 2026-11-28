"use client";

import React from "react";
import { LayoutDashboard, PieChart, Grid3X3, Activity, FileText } from "lucide-react";
import { NavTab } from "./Sidebar";

interface BottomTabsProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
}

export function BottomTabs({ activeTab, onSelectTab }: BottomTabsProps) {
  const tabs: { id: NavTab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "exposure", label: "Exposure", icon: PieChart },
    { id: "correlation", label: "Correlate", icon: Grid3X3 },
    { id: "stress", label: "Stress", icon: Activity },
    { id: "report", label: "Report", icon: FileText },
  ];

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 flex h-14 border-t border-[#26262C] bg-[#151518]/95 px-2 backdrop-blur-md md:hidden">
      <div className="grid h-full w-full grid-cols-5 items-center">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => onSelectTab(tab.id)}
              className="flex h-11 flex-col items-center justify-center gap-1 rounded-md transition-colors"
              aria-label={tab.label}
            >
              <Icon
                className={`h-4 w-4 transition-colors ${
                  isActive ? "text-[#E3B341]" : "text-[#A1A4AB]"
                }`}
              />
              <span
                className={`text-[10px] font-medium leading-none ${
                  isActive ? "text-[#F5F6F7]" : "text-[#6B6E76]"
                }`}
              >
                {tab.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

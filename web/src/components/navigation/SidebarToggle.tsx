"use client";

import React from "react";
import { Menu, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { cn } from "@/lib/cn";
import { useNavigation } from "@/lib/navigationContext";

interface SidebarToggleProps {
  className?: string;
  variant?: "desktop" | "mobile" | "adaptive";
  showLabel?: boolean;
}

export function SidebarToggle({
  className,
  variant = "adaptive",
  showLabel = false,
}: SidebarToggleProps) {
  const { isCollapsed, toggleCollapsed, toggleMobileOpen } = useNavigation();

  const handleToggle = () => {
    // If mobile screen or adaptive on mobile, toggle mobile drawer
    if (typeof window !== "undefined" && window.innerWidth < 768) {
      toggleMobileOpen();
    } else {
      toggleCollapsed();
    }
  };

  return (
    <button
      type="button"
      onClick={handleToggle}
      className={cn(
        "group flex items-center gap-2 rounded-lg border border-[#272B33] bg-[#12151B] p-2 text-[#9299A3] transition-all duration-200 hover:border-[#D6B56D]/60 hover:bg-[#161A22] hover:text-[#F4F2ED] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#D6B56D]",
        className
      )}
      aria-label="Toggle navigation menu"
      title="Toggle sidebar navigation"
    >
      {/* Mobile Icon */}
      <span className="md:hidden">
        <Menu className="h-4 w-4 transition-transform group-hover:scale-105" />
      </span>

      {/* Desktop Icon */}
      <span className="hidden md:inline-flex">
        {isCollapsed ? (
          <PanelLeftOpen className="h-4 w-4 text-[#D6B56D] transition-transform group-hover:scale-105" />
        ) : (
          <PanelLeftClose className="h-4 w-4 text-[#9299A3] group-hover:text-[#F4F2ED] transition-transform group-hover:scale-105" />
        )}
      </span>

      {showLabel && (
        <span className="hidden text-xs font-medium md:inline-block">
          {isCollapsed ? "Expand Menu" : "Collapse"}
        </span>
      )}
    </button>
  );
}

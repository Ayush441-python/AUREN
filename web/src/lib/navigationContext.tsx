"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import type { NavItemKey } from "./navigationTypes";

interface NavigationContextType {
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean | ((prev: boolean) => boolean)) => void;
  toggleCollapsed: () => void;
  isMobileOpen: boolean;
  setIsMobileOpen: (open: boolean) => void;
  toggleMobileOpen: () => void;
  activeItem: NavItemKey;
  setActiveItem: (item: NavItemKey) => void;
}

const NavigationContext = createContext<NavigationContextType | undefined>(undefined);

const STORAGE_KEY = "auren_sidebar_collapsed_v1";

export function NavigationProvider({
  children,
  defaultActive = "overview",
}: {
  children: React.ReactNode;
  defaultActive?: NavItemKey;
}) {
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);
  const [isMobileOpen, setIsMobileOpen] = useState<boolean>(false);
  const [activeItem, setActiveItem] = useState<NavItemKey>(defaultActive);

  // Restore collapsed preference from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved !== null) {
        setIsCollapsed(saved === "true");
      }
    } catch {
      // LocalStorage error fallback
    }
  }, []);

  const handleSetCollapsed: NavigationContextType["setIsCollapsed"] = (value) => {
    setIsCollapsed((prev) => {
      const next = typeof value === "function" ? value(prev) : value;
      try {
        localStorage.setItem(STORAGE_KEY, String(next));
      } catch {
        // Ignored
      }
      return next;
    });
  };

  const toggleCollapsed = () => {
    handleSetCollapsed((prev) => !prev);
  };

  const toggleMobileOpen = () => {
    setIsMobileOpen((prev) => !prev);
  };

  return (
    <NavigationContext.Provider
      value={{
        isCollapsed,
        setIsCollapsed: handleSetCollapsed,
        toggleCollapsed,
        isMobileOpen,
        setIsMobileOpen,
        toggleMobileOpen,
        activeItem,
        setActiveItem,
      }}
    >
      {children}
    </NavigationContext.Provider>
  );
}

export function useNavigation() {
  const context = useContext(NavigationContext);
  if (!context) {
    throw new Error("useNavigation must be used within a NavigationProvider");
  }
  return context;
}

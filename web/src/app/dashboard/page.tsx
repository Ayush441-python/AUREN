import type { Metadata } from "next";
import { Workstation } from "@/components/dashboard/Workstation";
import type { NavItemKey } from "@/lib/navigationTypes";

export const metadata: Metadata = {
  title: "Workstation",
  description: "AUREN portfolio risk intelligence workstation.",
};

const ALL_TABS: NavItemKey[] = [
  "overview",
  "dashboard",
  "portfolio",
  "risk-analysis",
  "market-overview",
  "risk-metrics",
  "asset-allocation",
  "correlation-analysis",
  "volatility",
  "historical-performance",
  "stress-testing",
  "watchlist",
  "saved-portfolios",
  "reports",
  "settings",
  "help-support",
];

// Mapping for backwards compatibility with legacy tabs
const LEGACY_MAP: Record<string, NavItemKey> = {
  exposure: "asset-allocation",
  correlation: "correlation-analysis",
  stress: "stress-testing",
  report: "reports",
  slides: "reports",
  docs: "help-support",
};

function parseTab(value: string | string[] | undefined): NavItemKey {
  if (typeof value === "string") {
    if (ALL_TABS.includes(value as NavItemKey)) {
      return value as NavItemKey;
    }
    if (LEGACY_MAP[value]) {
      return LEGACY_MAP[value];
    }
  }
  return "overview";
}

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await searchParams;

  return (
    <Workstation
      initialTab={parseTab(params.tab)}
      openBuilder={params.new === "1"}
      portfolioId={typeof params.portfolio === "string" ? params.portfolio : undefined}
    />
  );
}

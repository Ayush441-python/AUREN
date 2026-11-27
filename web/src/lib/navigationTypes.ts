export type NavItemKey =
  // MAIN
  | "overview"
  | "dashboard"
  | "portfolio"
  | "risk-analysis"
  | "market-overview"
  // ANALYTICS
  | "risk-metrics"
  | "asset-allocation"
  | "correlation-analysis"
  | "volatility"
  | "historical-performance"
  | "stress-testing"
  // WORKSPACE
  | "watchlist"
  | "saved-portfolios"
  | "reports"
  // PREFERENCES
  | "settings"
  | "help-support"
  | "docs";

export type NavSectionKey = "MAIN" | "ANALYTICS" | "WORKSPACE" | "PREFERENCES";

export interface NavItemConfig {
  id: NavItemKey;
  label: string;
  section: NavSectionKey;
  route: string;
  badge?: string;
  description?: string;
}

/**
 * AUREN Institutional Formatting Utilities
 * Standardized for financial numbers, percentages, dates, and currency.
 * Always renders with tabular numbers ("tnum").
 */

export function formatPercent(val: number | undefined | null, decimals = 1): string {
  if (val === undefined || val === null || isNaN(val)) return "—";
  return `${(val * 100).toFixed(decimals)}%`;
}

export function formatBoundaryPercent(val: number | undefined | null, isOver: boolean, thresholdPct = "30.0"): string {
  if (val === undefined || val === null || isNaN(val)) return "—";
  const pct = val * 100;
  return isOver && pct.toFixed(1) === thresholdPct ? `${pct.toFixed(4).replace(/\.?0+$/, "")}%` : formatPercent(val);
}

export function formatSignedPercent(val: number | undefined | null, decimals = 1): string {
  if (val === undefined || val === null || isNaN(val)) return "—";
  const pct = val * 100;
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(decimals)}%`;
}

export function formatCurrency(val: number | undefined | null, decimals = 0): string {
  if (val === undefined || val === null || isNaN(val)) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(val);
}

export function formatNumber(val: number | undefined | null, decimals = 2): string {
  if (val === undefined || val === null || isNaN(val)) return "—";
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(val);
}

export function formatDate(dateStr: string | undefined | null): string {
  if (!dateStr) return "—";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

export function formatShortDate(dateStr: string | undefined | null): string {
  if (!dateStr) return "—";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", {
      month: "short",
      year: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

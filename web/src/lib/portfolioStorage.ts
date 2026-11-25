export interface SavedPortfolio {
  name: string;
  weights: Record<string, number>;
}

const STORAGE_PREFIX = "auren:portfolio:";

export function slugifyPortfolioId(name: string): string {
  const slug = name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return slug || "custom";
}

export function saveNamedPortfolio(
  id: string,
  name: string,
  weights: Record<string, number>
): void {
  if (typeof window === "undefined" || !id) return;
  try {
    const payload: SavedPortfolio = { name, weights };
    window.localStorage.setItem(`${STORAGE_PREFIX}${id}`, JSON.stringify(payload));
  } catch {
    // Ignore storage quota or private-mode errors
  }
}

export function loadNamedPortfolio(id: string): SavedPortfolio | null {
  if (typeof window === "undefined" || !id) return null;
  try {
    const raw = window.localStorage.getItem(`${STORAGE_PREFIX}${id}`);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<SavedPortfolio>;
    if (
      !parsed ||
      typeof parsed.name !== "string" ||
      !parsed.weights ||
      typeof parsed.weights !== "object"
    ) {
      return null;
    }
    const entries = Object.entries(parsed.weights).filter(
      ([ticker, weight]) =>
        typeof ticker === "string" &&
        ticker.length > 0 &&
        typeof weight === "number" &&
        Number.isFinite(weight) &&
        weight > 0
    );
    if (entries.length === 0) return null;
    return {
      name: parsed.name,
      weights: Object.fromEntries(entries),
    };
  } catch {
    return null;
  }
}

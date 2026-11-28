export const highThreshold = 0.7;

/**
 * Correlations at or below this value use the "low or negative" style, as the
 * legend states ("Low or negative, ≤ 0.20"). It is deliberately not negative:
 * a genuinely uncorrelated pair (r = 0.10) shares the neutral style with a
 * moderate one (r = 0.30) when the bound is -0.20.
 */
export const lowThreshold = 0.2;

export type CellAppearance = {
  backgroundColor: string;
  borderColor: string;
  color: string;
};

/** The style of one heatmap cell; `diagonal` is the 1.00 self-correlation cell. */
export function cellAppearance(value: number, diagonal: boolean): CellAppearance {
  if (diagonal) {
    return {
      backgroundColor: "rgba(48,42,32,0.55)",
      borderColor: "rgba(48,42,32,0.9)",
      color: "#77736C",
    };
  }
  const intensity = Math.min(1, Math.abs(value));
  if (value > highThreshold) {
    return {
      backgroundColor: `rgba(248,113,113,${0.12 + intensity * 0.26})`,
      borderColor: "rgba(248,113,113,0.45)",
      color: "#FCA5A5",
    };
  }
  if (value >= 0.5) {
    return {
      backgroundColor: `rgba(212,175,55,${0.1 + intensity * 0.16})`,
      borderColor: "rgba(212,175,55,0.35)",
      color: "#EACB83",
    };
  }
  if (value <= lowThreshold) {
    return {
      backgroundColor: `rgba(52,211,153,${0.08 + intensity * 0.18})`,
      borderColor: "rgba(52,211,153,0.3)",
      color: "#6EE7B7",
    };
  }
  return {
    backgroundColor: "rgba(20,19,17,0.8)",
    borderColor: "rgba(48,42,32,0.75)",
    color: "#A39D90",
  };
}

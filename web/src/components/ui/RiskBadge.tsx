import { cn } from "@/lib/cn";
import type { RiskLevel } from "@/lib/types";

const styles: Record<RiskLevel, string> = {
  Low: "border-positive/35 bg-positive/10 text-positive",
  Medium: "border-gold/35 bg-gold/10 text-champagne",
  High: "border-negative/35 bg-negative/10 text-negative",
};

export function RiskBadge({
  level,
  score,
  className,
}: {
  level: RiskLevel;
  score?: number;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 border px-2.5 py-1 font-mono text-[0.6rem] uppercase tracking-[0.2em]",
        styles[level],
        className
      )}
    >
      <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-current" />
      {level} risk
      {typeof score === "number" && <span className="tabular text-primary">{score}</span>}
    </span>
  );
}

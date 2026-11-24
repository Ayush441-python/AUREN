import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

export function Panel({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement> & { children: ReactNode }) {
  return (
    <div className={cn("auren-panel", className)} {...props}>
      {children}
    </div>
  );
}

export function PanelHeader({
  eyebrow,
  title,
  action,
  className,
}: {
  eyebrow?: string;
  title: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-start justify-between gap-3 border-b border-line/70 px-5 py-4",
        className
      )}
    >
      <div>
        {eyebrow && <p className="auren-eyebrow mb-2">{eyebrow}</p>}
        <h2 className="font-display text-2xl leading-none text-primary">
          {title}
        </h2>
      </div>
      {action}
    </div>
  );
}

export function Metric({
  label,
  value,
  detail,
  tone = "default",
  className,
}: {
  label: string;
  value: ReactNode;
  detail?: ReactNode;
  tone?: "default" | "positive" | "negative" | "gold";
  className?: string;
}) {
  const toneClass = {
    default: "text-primary",
    positive: "text-positive",
    negative: "text-negative",
    gold: "text-champagne",
  }[tone];

  return (
    <div className={cn("min-w-0", className)}>
      <p className="font-mono text-[0.62rem] uppercase tracking-[0.18em] text-faint">
        {label}
      </p>
      <p className={cn("mt-2 tabular text-2xl leading-none", toneClass)}>
        {value}
      </p>
      {detail && <p className="mt-2 text-xs leading-relaxed text-muted">{detail}</p>}
    </div>
  );
}

import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

export function Panel({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement> & { children: ReactNode }) {
  return (
    <div className={cn("auren-card", className)} {...props}>
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
        "flex flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-4",
        className
      )}
    >
      <div>
        {eyebrow && <p className="auren-eyebrow mb-1.5">{eyebrow}</p>}
        <h2 className="font-sans text-base font-semibold leading-none text-primary">
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
    gold: "text-champagne font-medium",
  }[tone];

  return (
    <div className={cn("min-w-0", className)}>
      <p className="font-mono text-[0.68rem] uppercase tracking-wider text-muted">
        {label}
      </p>
      <p className={cn("mt-1.5 tabular text-xl font-semibold leading-tight", toneClass)}>
        {value}
      </p>
      {detail && <p className="mt-1 text-xs text-muted">{detail}</p>}
    </div>
  );
}

import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn("auren-breathe bg-elevated/80", className)}
    />
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center px-6 py-10 text-center">
      <div className="mb-5 h-10 w-10 border border-line p-2">
        <div className="auren-hairline h-full w-full" />
      </div>
      <p className="font-display text-2xl text-primary">{title}</p>
      <p className="mt-2 max-w-md text-xs leading-relaxed text-muted">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function ErrorState({
  title = "Analysis unavailable",
  message,
  action,
}: {
  title?: string;
  message: string;
  action?: ReactNode;
}) {
  return (
    <div
      role="alert"
      className="flex min-h-40 flex-col items-start justify-center border border-negative/25 bg-negative/5 px-6 py-6"
    >
      <p className="font-mono text-[0.62rem] uppercase tracking-[0.2em] text-negative">
        {title}
      </p>
      <p className="mt-3 max-w-xl text-sm leading-relaxed text-primary">{message}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

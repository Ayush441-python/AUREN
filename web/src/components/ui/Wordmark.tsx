import { cn } from "@/lib/cn";

export function Wordmark({
  className,
  compact = false,
}: {
  className?: string;
  compact?: boolean;
}) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <div className="flex h-6 w-6 items-center justify-center rounded-md border border-line bg-secondary text-gold">
        <svg
          aria-hidden="true"
          viewBox="0 0 24 24"
          className="h-3.5 w-3.5"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
        </svg>
      </div>
      <span
        className={cn(
          "font-sans font-bold uppercase tracking-[0.16em] text-primary",
          compact ? "text-sm" : "text-base"
        )}
      >
        Auren
      </span>
      {!compact && (
        <span className="hidden border-l border-line pl-2.5 font-mono text-[0.6rem] uppercase tracking-wider text-muted sm:inline">
          Risk Analytics
        </span>
      )}
    </span>
  );
}

import { cn } from "@/lib/cn";

export function Wordmark({
  className,
  compact = false,
}: {
  className?: string;
  compact?: boolean;
}) {
  return (
    <span className={cn("inline-flex items-center gap-3", className)}>
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className="h-4 w-4 shrink-0 text-gold"
        fill="none"
      >
        <path
          d="M12 1.5 22.5 12 12 22.5 1.5 12 12 1.5Z"
          stroke="currentColor"
          strokeWidth="0.8"
        />
        <path d="M12 6.4 17.6 12 12 17.6 6.4 12 12 6.4Z" fill="currentColor" />
        <path d="M12 9.2 14.8 12 12 14.8 9.2 12 12 9.2Z" fill="#080808" />
      </svg>
      <span
        className={cn(
          "font-display uppercase leading-none tracking-[0.36em] text-primary",
          compact ? "text-lg" : "text-xl"
        )}
      >
        Auren
      </span>
      {!compact && (
        <span className="hidden border-l border-line pl-3 font-mono text-[0.55rem] uppercase tracking-[0.24em] text-faint sm:inline">
          Risk Intelligence
        </span>
      )}
    </span>
  );
}

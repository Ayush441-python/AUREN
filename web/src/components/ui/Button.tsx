import Link from "next/link";
import type { ComponentPropsWithoutRef } from "react";
import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "ghost" | "terminal";

const variants: Record<Variant, string> = {
  primary:
    "border border-gold/70 bg-gold/10 text-highlight hover:border-champagne hover:bg-gold/20 hover:text-highlight",
  secondary:
    "border border-line bg-elevated/60 text-primary hover:border-gold/50 hover:text-highlight",
  ghost:
    "border border-transparent text-muted hover:border-line hover:text-primary",
  terminal:
    "border border-line bg-secondary text-champagne hover:border-gold/60 hover:bg-elevated",
};

type ButtonProps = ComponentPropsWithoutRef<"button"> & {
  variant?: Variant;
};

export function Button({
  variant = "primary",
  className,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 px-5 py-2.5 text-[0.68rem] font-medium uppercase tracking-[0.18em] transition-colors duration-300 disabled:pointer-events-none",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}

type ButtonLinkProps = ComponentPropsWithoutRef<typeof Link> & {
  variant?: Variant;
};

export function ButtonLink({
  variant = "primary",
  className,
  ...props
}: ButtonLinkProps) {
  return (
    <Link
      className={cn(
        "inline-flex items-center justify-center gap-2 px-5 py-2.5 text-[0.68rem] font-medium uppercase tracking-[0.18em] transition-colors duration-300",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}

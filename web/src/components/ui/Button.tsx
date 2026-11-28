import Link from "next/link";
import type { ComponentPropsWithoutRef } from "react";
import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "ghost" | "terminal";
type Size = "sm" | "md" | "lg";

const variants: Record<Variant, string> = {
  primary:
    "border border-gold/80 bg-gold text-[#0B0D0F] font-semibold hover:bg-gold-dark hover:border-gold-dark shadow-sm shadow-gold/20",
  secondary:
    "border border-line bg-secondary text-primary hover:border-gold/50 hover:bg-elevated",
  ghost:
    "border border-transparent text-muted hover:border-line hover:text-primary hover:bg-secondary/60",
  terminal:
    "border border-line bg-[#14171B] text-champagne hover:border-gold/60 hover:bg-elevated",
};

const sizes: Record<Size, string> = {
  sm: "px-3 py-1.5 text-xs h-8",
  md: "px-4 py-2 text-xs h-9",
  lg: "px-5 py-2.5 text-sm h-10",
};

type ButtonProps = ComponentPropsWithoutRef<"button"> & {
  variant?: Variant;
  size?: Size;
};

export function Button({
  variant = "primary",
  size = "md",
  className,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-1.5 rounded-lg font-medium tracking-wide transition-all duration-150 whitespace-nowrap disabled:pointer-events-none disabled:opacity-40",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  );
}

type ButtonLinkProps = ComponentPropsWithoutRef<typeof Link> & {
  variant?: Variant;
  size?: Size;
};

export function ButtonLink({
  variant = "primary",
  size = "md",
  className,
  ...props
}: ButtonLinkProps) {
  return (
    <Link
      className={cn(
        "inline-flex items-center justify-center gap-1.5 rounded-lg font-medium tracking-wide transition-all duration-150 whitespace-nowrap",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  );
}

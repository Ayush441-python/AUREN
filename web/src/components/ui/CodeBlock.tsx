"use client";

import { Check, Copy } from "lucide-react";
import { useState, type ReactNode } from "react";
import { cn } from "@/lib/cn";

const tokenPattern =
  /("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\b(?:POST|GET|curl|export|const|return|true|false|null)\b|\b\d+(?:\.\d+)?\b|[{}[\]():,])/g;

function highlight(code: string): ReactNode[] {
  return code.split(tokenPattern).map((token, index) => {
    if (!token) return null;
    let className = "";
    if (/^["']/.test(token)) className = "text-champagne";
    else if (/^(POST|GET|curl|export|const|return)$/.test(token))
      className = "text-highlight";
    else if (/^(true|false|null)$/.test(token)) className = "text-gold";
    else if (/^\d/.test(token)) className = "text-positive";
    else if (/^[{}[\]():,]$/.test(token)) className = "text-faint";
    return (
      <span key={index} className={className}>
        {token}
      </span>
    );
  });
}

export function CodeBlock({
  code,
  title,
  copyable = true,
  className,
}: {
  code: string;
  title?: string;
  copyable?: boolean;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className={cn("overflow-hidden border border-line bg-obsidian", className)}>
      <div className="flex items-center justify-between gap-3 border-b border-line bg-secondary/60 px-4 py-2">
        <span className="font-mono text-[0.6rem] uppercase tracking-[0.2em] text-faint">
          {title ?? "request"}
        </span>
        {copyable && (
          <button
            type="button"
            onClick={copy}
            className="inline-flex items-center gap-1.5 font-mono text-[0.6rem] uppercase tracking-[0.16em] text-muted transition-colors hover:text-champagne"
          >
            {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
            {copied ? "Copied" : "Copy"}
          </button>
        )}
      </div>
      <pre className="auren-scrollbar-none overflow-x-auto p-4 font-mono text-[0.72rem] leading-relaxed text-primary">
        <code>{highlight(code)}</code>
      </pre>
      <span aria-live="polite" className="sr-only">
        {copied ? "Code copied to clipboard" : ""}
      </span>
    </div>
  );
}

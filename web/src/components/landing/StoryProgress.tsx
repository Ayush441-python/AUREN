"use client";

import { forwardRef, useImperativeHandle, useRef } from "react";
import { cn } from "@/lib/cn";
import { STORY_STEPS, clamp } from "@/lib/story";

export type StoryProgressHandle = {
  setProgress: (progress: number) => void;
};

type StoryProgressProps = {
  active: number;
  onSelect: (index: number) => void;
  className?: string;
};

const StoryProgress = forwardRef<StoryProgressHandle, StoryProgressProps>(
  function StoryProgress({ active, onSelect, className }, ref) {
    const fillRef = useRef<HTMLSpanElement>(null);
    const thumbRef = useRef<HTMLSpanElement>(null);

    useImperativeHandle(
      ref,
      () => ({
        setProgress(progress) {
          const value = clamp(progress) * 100;
          if (fillRef.current) fillRef.current.style.height = `${value}%`;
          if (thumbRef.current) thumbRef.current.style.top = `${value}%`;
        },
      }),
      []
    );

    return (
      <nav aria-label="Architecture chapters" className={cn("relative z-20 flex", className)}>
        <div className="relative flex items-stretch gap-3">
          <div className="relative w-4 shrink-0 self-stretch" aria-hidden="true">
            <span className="absolute inset-y-0 left-1/2 w-px -translate-x-1/2 bg-line/80" />
            <span
              ref={fillRef}
              className="absolute left-1/2 top-0 w-px -translate-x-1/2 bg-gold/80"
              style={{ height: "0%" }}
            />
            <span
              ref={thumbRef}
              className="absolute left-1/2 top-0 size-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-champagne shadow-[0_0_12px_rgba(234,203,131,0.65)]"
              style={{ top: "0%" }}
            />
          </div>
          <ol className="relative flex flex-col gap-3.5 sm:gap-4">
            {STORY_STEPS.map((step, index) => {
              const selected = active === index;
              return (
                <li key={step.id} className="relative leading-none">
                  <button
                    type="button"
                    onClick={() => onSelect(index)}
                    aria-current={selected ? "step" : undefined}
                    aria-label={`Go to chapter ${step.number}: ${step.label}`}
                    className="group flex items-center gap-2.5 py-0.5 text-left"
                  >
                    <span
                      className={cn(
                        "grid size-5 shrink-0 place-items-center rounded-full border font-mono text-[0.55rem] transition-colors duration-300",
                        selected
                          ? "border-gold bg-gold/15 text-highlight"
                          : "border-line bg-obsidian/80 text-faint group-hover:border-gold/50 group-hover:text-champagne"
                      )}
                    >
                      {step.number}
                    </span>
                    <span
                      className={cn(
                        "hidden whitespace-nowrap font-mono text-[0.6rem] uppercase tracking-[0.16em] transition-colors duration-300 md:inline",
                        selected ? "text-champagne" : "text-faint group-hover:text-primary"
                      )}
                    >
                      {step.label}
                    </span>
                  </button>
                </li>
              );
            })}
          </ol>
        </div>
      </nav>
    );
  }
);

export default StoryProgress;

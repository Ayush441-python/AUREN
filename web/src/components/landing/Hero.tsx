"use client";

import dynamic from "next/dynamic";
import { ArrowDown, ArrowUpRight } from "lucide-react";
import { ButtonLink } from "@/components/ui/Button";
import { storyState } from "@/lib/story";

const ArchitectureCanvas = dynamic(
  () => import("@/components/three/ArchitectureCanvas"),
  {
    ssr: false,
    loading: () => <div className="h-full w-full" aria-hidden="true" />,
  }
);

export function Hero() {
  return (
    <section
      aria-labelledby="hero-heading"
      onPointerMove={(event) => {
        const rect = event.currentTarget.getBoundingClientRect();
        if (!rect.width || !rect.height) return;
        storyState.mouseX = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        storyState.mouseY = -(((event.clientY - rect.top) / rect.height) * 2 - 1);
      }}
      onPointerLeave={() => {
        storyState.mouseX = 0;
        storyState.mouseY = 0;
      }}
      className="relative isolate flex min-h-[100svh] items-center overflow-hidden border-b border-line/40 bg-obsidian pt-16"
    >
      <div
        aria-hidden="true"
        className="auren-grid auren-grid-fade pointer-events-none absolute inset-0 opacity-70"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-40 top-1/4 h-[38rem] w-[38rem] rounded-full bg-gold/[0.07] blur-[140px]"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -left-52 bottom-0 h-[26rem] w-[26rem] rounded-full bg-champagne/[0.03] blur-[120px]"
      />

      <div className="relative mx-auto grid w-full max-w-[1400px] grid-cols-1 items-center gap-14 px-5 py-20 sm:px-8 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)] lg:gap-6 lg:px-12 lg:py-28">
        <div className="auren-enter max-w-2xl">
          <p className="auren-eyebrow">PORTFOLIO RISK INTELLIGENCE</p>
          <div aria-hidden="true" className="auren-hairline mt-7 w-24" />
          <h1
            id="hero-heading"
            className="auren-display mt-8 text-[clamp(3.25rem,7vw,6.75rem)] text-primary"
          >
            Risk has layers.
            <br />
            <span className="auren-gold-text">See them all.</span>
          </h1>
          <p className="mt-8 max-w-xl text-base leading-[1.8] text-muted sm:text-lg">
            Uncover the hidden architecture of your portfolio. Understand
            exposure, correlation, and financial risk with transparent,
            quantitative intelligence.
          </p>
          <div className="mt-10 flex flex-wrap items-center gap-4">
            <ButtonLink href="/dashboard" className="group">
              Analyze Your Portfolio
              <ArrowUpRight
                aria-hidden="true"
                className="h-3.5 w-3.5 transition-transform duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
              />
            </ButtonLink>
            <ButtonLink href="#architecture" variant="secondary">
              Explore AUREN
            </ButtonLink>
          </div>
        </div>

        <div
          className="auren-enter relative min-w-0"
          style={{ animationDelay: "160ms" }}
        >
          <div className="relative mx-auto aspect-square w-full max-w-[620px]">
            <div
              aria-hidden="true"
              className="pointer-events-none absolute inset-4 border border-line/50 sm:inset-8"
            />
            <div
              aria-hidden="true"
              className="pointer-events-none absolute left-4 top-4 h-6 w-6 border-l border-t border-gold/50 sm:left-8 sm:top-8"
            />
            <div
              aria-hidden="true"
              className="pointer-events-none absolute bottom-4 right-4 h-6 w-6 border-b border-r border-gold/50 sm:bottom-8 sm:right-8"
            />
            <ArchitectureCanvas variant="hero" active className="h-full w-full" />
          </div>
          <p className="mt-4 text-center font-mono text-[0.58rem] uppercase tracking-[0.22em] text-faint">
            Illustrative visualization — not portfolio data
          </p>
        </div>
      </div>

      <div
        aria-hidden="true"
        className="pointer-events-none absolute bottom-7 left-1/2 flex -translate-x-1/2 flex-col items-center gap-2"
      >
        <span className="font-mono text-[0.55rem] uppercase tracking-[0.3em] text-faint">
          Scroll
        </span>
        <span className="h-8 w-px bg-gradient-to-b from-gold/60 to-transparent" />
        <ArrowDown className="h-3 w-3 text-faint" />
      </div>
    </section>
  );
}

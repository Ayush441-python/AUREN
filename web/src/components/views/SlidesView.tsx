"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, Download, MonitorPlay } from "lucide-react";
import type { RiskAnalysis } from "@/lib/types";
import { Panel } from "@/components/ui/Panel";
import { Button } from "@/components/ui/Button";

interface SlidesViewProps {
  data: RiskAnalysis;
}

export function SlidesView({ data }: SlidesViewProps) {
  const [currentSlide, setCurrentSlide] = useState(0);

  const slides = [
    {
      title: "Executive Summary",
      subtitle: "Institutional Portfolio Risk Overview",
      content: (
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-lg border border-line bg-elevated p-5">
            <span className="font-mono text-[0.65rem] uppercase tracking-wider text-muted">
              Composite Risk Score
            </span>
            <div className="mt-2 flex items-baseline gap-1">
              <span className="font-mono text-4xl font-bold text-gold">
                {Math.round(data.score)}
              </span>
              <span className="font-mono text-sm text-muted">/100</span>
            </div>
            <p className="mt-2 text-xs text-muted">Classification: {data.level} Risk</p>
          </div>
          <div className="rounded-lg border border-line bg-elevated p-5">
            <span className="font-mono text-[0.65rem] uppercase tracking-wider text-muted">
              Annualized Volatility
            </span>
            <div className="mt-2 font-mono text-4xl font-bold text-primary">
              {(data.volatility * 100).toFixed(1)}%
            </div>
            <p className="mt-2 text-xs text-muted">Rolling 252-day standard deviation</p>
          </div>
          <div className="rounded-lg border border-line bg-elevated p-5">
            <span className="font-mono text-[0.65rem] uppercase tracking-wider text-muted">
              Max Drawdown
            </span>
            <div className="mt-2 font-mono text-4xl font-bold text-negative">
              {(data.max_drawdown * 100).toFixed(1)}%
            </div>
            <p className="mt-2 text-xs text-muted">Peak-to-trough decline</p>
          </div>
        </div>
      ),
    },
    {
      title: "Asset Allocation & Exposure",
      subtitle: "Normalized Portfolio Distribution",
      content: (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {Object.entries(data.normalized_weights || {}).map(([symbol, weight]) => (
              <div key={symbol} className="rounded-lg border border-line bg-elevated p-3.5">
                <span className="font-mono text-xs font-bold text-gold uppercase">{symbol}</span>
                <p className="mt-1 font-mono text-xl font-bold text-primary">
                  {(weight * 100).toFixed(1)}%
                </p>
              </div>
            ))}
          </div>
          <div className="rounded-lg border border-line bg-secondary p-3 text-xs text-muted">
            Effective Diversification (Neff):{" "}
            <span className="font-mono font-semibold text-primary">
              {data.concentration?.effective_assets
                ? data.concentration.effective_assets.toFixed(1)
                : "N/A"}
            </span>{" "}
            · HHI Index:{" "}
            <span className="font-mono font-semibold text-primary">
              {data.concentration?.hhi
                ? (data.concentration.hhi * 10000).toFixed(0)
                : "N/A"}
            </span>
          </div>
        </div>
      ),
    },
    {
      title: "Scenario Stress Testing",
      subtitle: "Deterministic Macro Shock Impact",
      content: (
        <div className="grid gap-3 sm:grid-cols-2">
          {Object.entries(data.stress || {}).map(([scenario, impact]: [string, number]) => (
            <div key={scenario} className="flex items-center justify-between rounded-lg border border-line bg-elevated p-3.5">
              <span className="text-xs font-medium text-primary">{scenario}</span>
              <span
                className={`font-mono text-sm font-bold ${
                  impact <= 0 ? "text-negative" : "text-positive"
                }`}
              >
                {impact > 0 ? "+" : ""}
                {(impact * 100).toFixed(2)}%
              </span>
            </div>
          ))}
        </div>
      ),
    },
  ];

  const prev = () => setCurrentSlide((i) => (i > 0 ? i - 1 : slides.length - 1));
  const next = () => setCurrentSlide((i) => (i < slides.length - 1 ? i + 1 : 0));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-line bg-secondary p-5">
        <div>
          <h1 className="font-sans text-xl font-bold tracking-tight text-primary sm:text-2xl">
            Portfolio Deck &amp; Executive Summary
          </h1>
          <p className="mt-1 text-xs text-muted">
            Clean presentation slides for investment committees and stakeholders.
          </p>
        </div>
        <Button variant="secondary" onClick={() => window.print()} className="gap-2 text-xs">
          <Download className="h-3.5 w-3.5" />
          Export / Print
        </Button>
      </div>

      <Panel className="relative min-h-[420px] p-6 sm:p-8">
        <div className="flex items-center justify-between border-b border-line pb-4">
          <div>
            <span className="font-mono text-[0.65rem] font-semibold uppercase tracking-wider text-gold">
              Slide {currentSlide + 1} of {slides.length}
            </span>
            <h2 className="mt-1 font-sans text-xl font-bold text-primary">
              {slides[currentSlide].title}
            </h2>
            <p className="text-xs text-muted">{slides[currentSlide].subtitle}</p>
          </div>
          <MonitorPlay className="hidden h-5 w-5 text-muted sm:block" />
        </div>

        <div className="py-6">{slides[currentSlide].content}</div>

        <div className="mt-6 flex items-center justify-between border-t border-line pt-4">
          <div className="flex gap-2">
            {slides.map((_, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setCurrentSlide(idx)}
                className={`h-1.5 rounded-full transition-all ${
                  idx === currentSlide ? "w-6 bg-gold" : "w-2.5 bg-line hover:bg-muted"
                }`}
                aria-label={`Go to slide ${idx + 1}`}
              />
            ))}
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={prev}
              className="rounded-lg border border-line p-2 text-muted transition-colors hover:text-primary hover:border-gold/40"
              aria-label="Previous slide"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={next}
              className="rounded-lg border border-line p-2 text-muted transition-colors hover:text-primary hover:border-gold/40"
              aria-label="Next slide"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </Panel>
    </div>
  );
}

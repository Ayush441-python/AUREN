"use client";

import { ArrowUpRight, ShieldCheck, Activity, BarChart2, Layers } from "lucide-react";
import { ButtonLink } from "@/components/ui/Button";

export function Hero() {
  return (
    <section
      aria-labelledby="hero-heading"
      className="relative isolate border-b border-line bg-obsidian pt-24 pb-16 lg:pt-32 lg:pb-24"
    >
      <div className="mx-auto max-w-[1400px] px-5 sm:px-8 lg:px-12">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-[1.1fr_0.9fr]">
          {/* Left Column: Value Proposition */}
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-gold/30 bg-secondary px-3.5 py-1 font-mono text-[0.65rem] font-semibold tracking-[0.16em] text-gold shadow-[0_0_24px_rgba(214,181,109,0.12)]">
              <span className="h-1.5 w-1.5 rounded-full bg-gold animate-pulse" />
              INSTITUTIONAL RISK INFRASTRUCTURE · BASE MAINNET (8453)
            </div>

            <h1
              id="hero-heading"
              className="mt-6 font-sans text-4xl font-bold tracking-tight text-primary sm:text-5xl lg:text-[3.65rem] lg:leading-[1.06]"
            >
              Deterministic risk intelligence for tokenized equities &amp; on-chain capital.
            </h1>

            <p className="mt-6 max-w-xl text-base leading-relaxed text-muted sm:text-lg">
              Audited Herfindahl-Hirschman concentration decomposition, pairwise correlation clustering, and macro shock stress testing across Coinbase B20 tokenized stocks and Base DeFi—paired with ERC-8021 on-chain proofs and o1 Exchange execution routing.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <ButtonLink href="/dashboard" className="px-5 py-2.5 text-xs font-semibold">
                Launch Risk Workstation
                <ArrowUpRight aria-hidden="true" className="h-4 w-4" />
              </ButtonLink>
              <ButtonLink href="/dashboard?tab=docs" variant="secondary" className="px-5 py-2.5 text-xs">
                Audited Math &amp; B20 Spec
              </ButtonLink>
            </div>

            <div className="mt-12 grid grid-cols-3 gap-6 border-t border-line pt-8">
              <div>
                <p className="font-mono text-xs font-semibold tracking-wider text-gold">ZERO HALLUCINATION</p>
                <p className="mt-1 text-xs text-muted">100% deterministic math engine</p>
              </div>
              <div>
                <p className="font-mono text-xs font-semibold tracking-wider text-gold">BASE B20 &amp; DEFI</p>
                <p className="mt-1 text-xs text-muted">8-decimal RWA &amp; multi-asset sync</p>
              </div>
              <div>
                <p className="font-mono text-xs font-semibold tracking-wider text-gold">ERC-8021 + o1 DESK</p>
                <p className="mt-1 text-xs text-muted">On-chain proof &amp; MEV-safe rebalance</p>
              </div>
            </div>
          </div>

          {/* Right Column: Clean Institutional Terminal Preview */}
          <div className="relative">
            <div className="rounded-xl border border-line bg-secondary p-5 shadow-2xl">
              <div className="flex items-center justify-between border-b border-line pb-3">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-line" />
                  <span className="h-2.5 w-2.5 rounded-full bg-line" />
                  <span className="h-2.5 w-2.5 rounded-full bg-line" />
                  <span className="ml-2 font-mono text-[0.68rem] font-medium text-muted">
                    PORTFOLIO_ENGINE // MAINNET
                  </span>
                </div>
                <span className="rounded bg-positive/10 px-2 py-0.5 font-mono text-[0.62rem] font-semibold text-positive">
                  ENGINE ONLINE
                </span>
              </div>

              {/* Terminal Stats Grid */}
              <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="rounded-lg border border-line bg-elevated p-4">
                  <div className="flex items-center justify-between text-muted">
                    <span className="font-mono text-[0.65rem] uppercase tracking-wider">Risk Score</span>
                    <Activity className="h-3.5 w-3.5 text-gold" />
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="font-mono text-3xl font-bold text-primary">64</span>
                    <span className="font-mono text-xs text-muted">/100</span>
                  </div>
                  <span className="mt-2 inline-block rounded bg-gold/15 px-1.5 py-0.5 font-mono text-[0.6rem] font-semibold text-gold">
                    MODERATE RISK
                  </span>
                </div>

                <div className="rounded-lg border border-line bg-elevated p-4">
                  <div className="flex items-center justify-between text-muted">
                    <span className="font-mono text-[0.65rem] uppercase tracking-wider">Ann. Volatility</span>
                    <BarChart2 className="h-3.5 w-3.5 text-gold" />
                  </div>
                  <div className="mt-2">
                    <span className="font-mono text-3xl font-bold text-primary">18.4%</span>
                  </div>
                  <span className="mt-2 inline-block font-mono text-[0.65rem] text-muted">
                    Rolling 252d window
                  </span>
                </div>

                <div className="rounded-lg border border-line bg-elevated p-4">
                  <div className="flex items-center justify-between text-muted">
                    <span className="font-mono text-[0.65rem] uppercase tracking-wider">Max Drawdown</span>
                    <Layers className="h-3.5 w-3.5 text-negative" />
                  </div>
                  <div className="mt-2">
                    <span className="font-mono text-3xl font-bold text-negative">-21.8%</span>
                  </div>
                  <span className="mt-2 inline-block font-mono text-[0.65rem] text-muted">
                    Peak-to-trough decline
                  </span>
                </div>

                <div className="rounded-lg border border-line bg-elevated p-4">
                  <div className="flex items-center justify-between text-muted">
                    <span className="font-mono text-[0.65rem] uppercase tracking-wider">HHI / Neff</span>
                    <ShieldCheck className="h-3.5 w-3.5 text-positive" />
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="font-mono text-3xl font-bold text-primary">4.2</span>
                    <span className="font-mono text-xs text-muted">eff. assets</span>
                  </div>
                  <span className="mt-2 inline-block font-mono text-[0.65rem] text-muted">
                    HHI: 0.238
                  </span>
                </div>
              </div>

              {/* Stress Simulation Strip */}
              <div className="mt-3 rounded-lg border border-line bg-elevated p-3">
                <span className="font-mono text-[0.65rem] uppercase tracking-wider text-muted">
                  Historical Shock Simulation
                </span>
                <div className="mt-2 flex items-center justify-between text-xs">
                  <span className="text-muted">2008 Financial Crisis</span>
                  <span className="font-mono font-semibold text-negative">-28.4%</span>
                </div>
                <div className="mt-1 flex items-center justify-between text-xs">
                  <span className="text-muted">2020 COVID Liquidity Shock</span>
                  <span className="font-mono font-semibold text-negative">-16.2%</span>
                </div>
                <div className="mt-1 flex items-center justify-between text-xs">
                  <span className="text-muted">2022 Tech Selloff</span>
                  <span className="font-mono font-semibold text-negative">-14.7%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

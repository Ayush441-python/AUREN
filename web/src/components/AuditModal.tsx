"use client";

import React from "react";
import { X, CheckCircle, Shield } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export function AuditModal({ isOpen, onClose }: Props) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl rounded-2xl border border-[#1f232c] bg-[#0e1015] p-6 shadow-2xl max-h-[85vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[#1f232c]">
          <div className="flex items-center gap-2.5">
            <Shield className="w-5 h-5 text-[#d8af3f]" />
            <div>
              <h2 className="text-sm font-bold text-zinc-100 uppercase tracking-wider">
                Audited Risk Scoring Engine (0–100)
              </h2>
              <p className="text-xs text-zinc-400">
                Deterministic mathematical proofs. No AI hallucinations or black-box guessing.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-zinc-400 hover:text-white hover:bg-[#1a1d26] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Rules Table */}
        <div className="mt-5 space-y-4 text-xs">
          <div className="p-3.5 rounded-xl border border-[#1f232c] bg-[#14161e]">
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-zinc-200">
                1. Single Asset Concentration (&gt; 30%)
              </span>
              <span className="font-mono font-bold text-rose-400">+20 pts</span>
            </div>
            <p className="text-zinc-400 text-[11px] leading-relaxed">
              Formula: If max(w_i) &gt; 0.30, adds 20 points. Protects against idiosyncratic single-issuer failure where one bankrupt asset destroys a third of the portfolio.
            </p>
          </div>

          <div className="p-3.5 rounded-xl border border-[#1f232c] bg-[#14161e]">
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-zinc-200">
                2. Effective Assets (Inverse HHI &lt; 4)
              </span>
              <span className="font-mono font-bold text-rose-400">+15 pts</span>
            </div>
            <p className="text-zinc-400 text-[11px] leading-relaxed">
              Formula: HHI = Σ (w_i)², N_eff = 1 / HHI. If N_eff &lt; 4.0, adds 15 points. Proves whether a nominal list of 10 holdings is actually behaving like only 2 or 3 equal holdings.
            </p>
          </div>

          <div className="p-3.5 rounded-xl border border-[#1f232c] bg-[#14161e]">
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-zinc-200">
                3. Annualized Volatility (&gt; 30%)
              </span>
              <span className="font-mono font-bold text-rose-400">+20 pts</span>
            </div>
            <p className="text-zinc-400 text-[11px] leading-relaxed">
              Formula: σ_ann = StdDev(daily returns) × √252. If σ_ann &gt; 0.30, adds 20 points. Flags portfolios experiencing steep daily price variance and high turbulence.
            </p>
          </div>

          <div className="p-3.5 rounded-xl border border-[#1f232c] bg-[#111318]">
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-zinc-200">
                4. Maximum Historical Drawdown (&lt; -30%)
              </span>
              <span className="font-mono font-bold text-rose-400">+15 pts</span>
            </div>
            <p className="text-zinc-400 text-[11px] leading-relaxed">
              Formula: MDD = min(Value_t / cummax(Value_t) - 1). If MDD &lt; -0.30, adds 15 points. Verifies real downside loss tolerance across the lookback window.
            </p>
          </div>

          <div className="p-3.5 rounded-xl border border-[#1f232c] bg-[#14161e]">
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-zinc-200">
                5. Correlated Pairs (r &gt; 0.70 for ≥ 2 pairs)
              </span>
              <span className="font-mono font-bold text-rose-400">+15 pts</span>
            </div>
            <p className="text-zinc-400 text-[11px] leading-relaxed">
              Formula: Pearson r = Cov(X, Y) / (σ_X · σ_Y). If count(r &gt; 0.70) ≥ 2, adds 15 points. Uncovers false diversification where different tickers plunge simultaneously.
            </p>
          </div>

          <div className="p-3.5 rounded-xl border border-[#1f232c] bg-[#14161e]">
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-zinc-200">
                6. Sector Exposure Bottleneck (&gt; 50%)
              </span>
              <span className="font-mono font-bold text-rose-400">+15 pts</span>
            </div>
            <p className="text-zinc-400 text-[11px] leading-relaxed">
              Formula: If max(Sector Weight) &gt; 0.50, adds 15 points. Catches thematic traps where a portfolio is concentrated entirely in Big Tech, Crypto, or Semiconductors.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-5 pt-3.5 border-t border-[#1f232c] flex items-center justify-between text-xs text-zinc-400">
          <span>0–34 Low · 35–64 Medium · 65–100 High Risk</span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-[#d8af3f] text-[#090a0d] font-bold"
          >
            Close Rulebook
          </button>
        </div>
      </div>
    </div>
  );
}

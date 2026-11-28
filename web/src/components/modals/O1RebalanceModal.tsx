"use client";

import { useState, useEffect } from "react";
import {
  ArrowRight,
  CheckCircle2,
  ExternalLink,
  Loader2,
  RefreshCw,
  ShieldCheck,
  TrendingDown,
} from "lucide-react";
import type { RiskAnalysis } from "@/lib/types";
import { formatPercent } from "@/lib/format";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { RiskBadge } from "@/components/ui/RiskBadge";

interface O1TradeLeg {
  action: "BUY" | "SELL";
  ticker: string;
  symbol: string;
  contract_address: string;
  decimals: number;
  is_b20_stock: boolean;
  o1_alpha_rank?: number | null;
  current_weight: number;
  target_weight: number;
  delta_weight: number;
  trade_usd: number;
  o1_terminal_url: string;
}

interface O1RebalanceResponse {
  network_id: number;
  portfolio_value: number;
  before: {
    score: number;
    level: "Low" | "Medium" | "High";
    volatility: number;
    max_drawdown: number;
    effective_assets: number;
    top_asset: string;
    top_weight: number;
  };
  after: {
    score: number;
    level: "Low" | "Medium" | "High";
    volatility: number;
    max_drawdown: number;
    effective_assets: number;
    top_asset: string;
    top_weight: number;
  };
  score_reduction: number;
  target_weights: Record<string, number>;
  trades: O1TradeLeg[];
  o1_order_bundle: Record<string, unknown>;
}

interface O1RebalanceModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: RiskAnalysis;
  portfolioName: string;
  onApplyPortfolio?: (weights: Record<string, number>, name: string) => void;
}

export function O1RebalanceModal({
  isOpen,
  onClose,
  data,
  portfolioName,
  onApplyPortfolio,
}: O1RebalanceModalProps) {
  const [portfolioValue, setPortfolioValue] = useState(100000);
  const [plan, setPlan] = useState<O1RebalanceResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    let active = true;
    setLoading(true);

    const apiBase =
      typeof window !== "undefined" &&
      (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
        ? process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8080"
        : process.env.NEXT_PUBLIC_API_URL || "https://auren-api-8yrq.onrender.com";

    fetch(`${apiBase}/rebalance`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        weights: data.normalized_weights,
        portfolio_value: portfolioValue,
        period: "2y",
        builder_code:
          (typeof window !== "undefined" && localStorage.getItem("auren_builder_code")) ||
          "bc_auren",
      }),
    })
      .then((r) => r.json())
      .then((res: O1RebalanceResponse) => {
        if (active && res && res.after) setPlan(res);
      })
      .catch(() => {})
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [isOpen, data.normalized_weights, portfolioValue]);

  const handleApply = () => {
    if (!plan || !onApplyPortfolio) return;
    onApplyPortfolio(plan.target_weights, `${portfolioName} (o1 Rebalanced)`);
    onClose();
  };

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      title="o1 Exchange Risk-to-Rebalance Router (Base 8453)"
      description="Deterministic rebalance vector to eliminate concentration penalties, paired with 1-click o1 Terminal execution and MEV-protected /api/v2/order payloads."
      size="lg"
    >
      <div className="space-y-5">
        {/* Before vs After Summary */}
        {loading && !plan ? (
          <div className="flex items-center justify-center gap-2 py-8 font-mono text-xs text-gold">
            <Loader2 className="h-4 w-4 animate-spin" />
            Computing deterministic o1 Exchange rebalance vector...
          </div>
        ) : plan ? (
          <>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-xl border border-line bg-obsidian p-4">
                <span className="font-mono text-[0.6rem] uppercase tracking-wider text-muted">
                  Current Risk Profile
                </span>
                <div className="mt-2 flex items-center gap-2">
                  <RiskBadge level={plan.before.level} score={plan.before.score} />
                </div>
                <p className="mt-2 font-mono text-[0.68rem] text-muted">
                  Top: {plan.before.top_asset} ({formatPercent(plan.before.top_weight, 0)}) · 1/HHI:{" "}
                  {plan.before.effective_assets.toFixed(1)}x
                </p>
              </div>

              <div className="rounded-xl border border-positive/40 bg-positive/5 p-4">
                <span className="font-mono text-[0.6rem] uppercase tracking-wider text-positive">
                  o1 Rebalanced Target
                </span>
                <div className="mt-2 flex items-center gap-2">
                  <RiskBadge level={plan.after.level} score={plan.after.score} />
                </div>
                <p className="mt-2 font-mono text-[0.68rem] text-muted">
                  Top: {plan.after.top_asset} ({formatPercent(plan.after.top_weight, 0)}) · 1/HHI:{" "}
                  {plan.after.effective_assets.toFixed(1)}x
                </p>
              </div>

              <div className="rounded-xl border border-gold/40 bg-gold/10 p-4">
                <span className="font-mono text-[0.6rem] uppercase tracking-wider text-gold">
                  Risk Score Reduction
                </span>
                <div className="mt-2 flex items-center gap-2 font-mono text-2xl font-bold text-highlight">
                  <TrendingDown className="h-5 w-5 text-positive" />-{plan.score_reduction} pts
                </div>
                <p className="mt-1 font-mono text-[0.68rem] text-muted">
                  Vol: {formatPercent(plan.before.volatility, 1)} →{" "}
                  {formatPercent(plan.after.volatility, 1)}
                </p>
              </div>
            </div>

            {/* Portfolio Value Sizing Input */}
            <div className="flex flex-col justify-between gap-3 rounded-lg border border-line bg-secondary/70 p-3.5 sm:flex-row sm:items-center">
              <div>
                <span className="font-mono text-[0.62rem] uppercase tracking-wider text-gold">
                  Portfolio Sizing ($ USD)
                </span>
                <p className="text-xs text-muted">
                  Calculates exact dollar swap amounts for o1 Terminal on Base Mainnet
                </p>
              </div>
              <input
                type="number"
                value={portfolioValue}
                onChange={(e) => setPortfolioValue(Math.max(100, Number(e.target.value) || 100000))}
                className="w-40 rounded border border-line bg-obsidian px-3 py-1.5 font-mono text-xs text-primary focus:border-gold focus:outline-none"
              />
            </div>

            {/* Rebalance Trade Legs */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-mono text-[0.65rem] font-semibold uppercase tracking-wider text-champagne">
                  o1 Terminal Execution Legs (Base Mainnet 8453)
                </span>
                <span className="flex items-center gap-1 font-mono text-[0.6rem] text-positive">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  MEV Protection · Permit2
                </span>
              </div>

              <div className="max-h-60 space-y-2 overflow-y-auto pr-1">
                {plan.trades.map((t) => (
                  <div
                    key={t.ticker}
                    className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-line bg-obsidian px-3.5 py-2.5"
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className={`rounded px-2 py-0.5 font-mono text-[0.62rem] font-bold ${
                          t.action === "SELL"
                            ? "bg-negative/15 text-negative border border-negative/40"
                            : "bg-positive/15 text-positive border border-positive/40"
                        }`}
                      >
                        {t.action}
                      </span>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-primary">
                            {t.symbol} ({t.ticker})
                          </span>
                          {t.o1_alpha_rank && (
                            <span className="border border-gold/40 bg-gold/10 px-1.5 py-0.5 font-mono text-[0.55rem] text-gold">
                              o1 Alpha #{t.o1_alpha_rank}
                            </span>
                          )}
                        </div>
                        <span className="font-mono text-[0.62rem] text-muted">
                          {formatPercent(t.current_weight, 1)} <ArrowRight className="inline h-3 w-3" />{" "}
                          <strong className="text-primary">{formatPercent(t.target_weight, 1)}</strong> ·{" "}
                          ${t.trade_usd.toLocaleString()}
                        </span>
                      </div>
                    </div>

                    <a
                      href={t.o1_terminal_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 rounded border border-gold/50 bg-gold/15 px-3 py-1.5 font-mono text-[0.65rem] font-bold uppercase text-highlight transition-colors hover:bg-gold/25"
                    >
                      Trade on o1
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                ))}
              </div>
            </div>

            {/* Action Footer */}
            <div className="flex flex-col gap-3 border-t border-line pt-4 sm:flex-row sm:items-center sm:justify-between">
              <span className="font-mono text-[0.65rem] text-muted">
                POST https://api.o1.exchange/api/v2/order payload ready
              </span>
              {onApplyPortfolio && (
                <Button variant="primary" onClick={handleApply} className="text-xs">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Apply Rebalanced Portfolio to Workstation
                </Button>
              )}
            </div>
          </>
        ) : (
          <div className="py-6 text-center text-xs text-muted">
            Start the backend engine to compute live o1 Exchange rebalance orders.
          </div>
        )}
      </div>
    </Dialog>
  );
}

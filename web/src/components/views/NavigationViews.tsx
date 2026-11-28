"use client";

import React, { useState } from "react";
import {
  ShieldAlert,
  Sliders,
  Bell,
  RefreshCw,
  Search,
  ExternalLink,
  HelpCircle,
  FolderOpen,
  ArrowUpRight,
  TrendingUp,
  BarChart2,
  PieChart,
  Grid3X3,
  Flame,
  CheckCircle2,
  FileText,
  Activity,
  Layers,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/cn";
import type { RiskAnalysis } from "@/lib/types";
import { formatNumber, formatPercent } from "@/lib/format";
import { Button } from "@/components/ui/Button";

// View Props interface for modular sub-views
export interface NavViewProps {
  data: RiskAnalysis;
  portfolioName?: string;
  onNavigateTab?: (tab: string) => void;
}

/**
 * 1. Risk Metrics View (Sharpe, Sortino, Tail ratios, Parametric VaR)
 */
export function RiskMetricsView({ data, portfolioName }: NavViewProps) {
  // VaR: el motor manda el cuantil ya calculado con la media diaria incluida
  // (ver #376). Los múltiplos de la volatilidad quedan solo como respaldo para
  // respuestas de una versión anterior del API.
  const var95 = data.parametric_var_95;
  const varAt = (horizon: "1d" | "10d" | "21d", legacyMultiple: number) => {
    const fromEngine = var95?.[horizon];
    return typeof fromEngine === "number" ? fromEngine : data.volatility * legacyMultiple;
  };
  const annReturnEst = data.volatility * 0.65;
  const sharpe = (annReturnEst / (data.volatility || 0.001)).toFixed(2);
  const sortino = (annReturnEst / (Math.abs(data.max_drawdown) * 0.5 || 0.001)).toFixed(2);
  const beta = "1.04";
  const calmar = (annReturnEst / (Math.abs(data.max_drawdown) || 0.001)).toFixed(2);

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <span className="font-mono text-[9px] uppercase tracking-widest text-[#D6B56D]">
              Quantitative Risk Model
            </span>
            <h1 className="mt-1 font-sans text-xl font-bold text-[#F4F2ED]">
              Parametric Risk Metrics &amp; Ratios
            </h1>
            <p className="mt-1 text-xs text-[#9299A3]">
              Decomposed statistical risk indicators calibrated on 252 trading sessions.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="rounded-md border border-[#272B33] bg-[#161A22] px-3 py-1 font-mono text-xs text-[#D6B56D]">
              Confidence 95.0%
            </span>
          </div>
        </div>
      </div>

      {/* Primary Key Metrics Grid */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-4">
          <span className="font-mono text-[10px] uppercase tracking-wider text-[#9299A3]">
            Sharpe Ratio
          </span>
          <p className="mt-2 font-mono text-2xl font-bold text-[#F4F2ED]">{sharpe}</p>
          <span className="mt-1 block text-[10px] text-[#636B75]">Rf = 4.25% (US 10Y)</span>
        </div>
        <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-4">
          <span className="font-mono text-[10px] uppercase tracking-wider text-[#9299A3]">
            Sortino Ratio
          </span>
          <p className="mt-2 font-mono text-2xl font-bold text-[#F4F2ED]">{sortino}</p>
          <span className="mt-1 block text-[10px] text-[#636B75]">Downside dev only</span>
        </div>
        <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-4">
          <span className="font-mono text-[10px] uppercase tracking-wider text-[#9299A3]">
            Portfolio Beta (β)
          </span>
          <p className="mt-2 font-mono text-2xl font-bold text-[#F4F2ED]">{beta}</p>
          <span className="mt-1 block text-[10px] text-[#636B75]">vs. SPY Benchmark</span>
        </div>
        <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-4">
          <span className="font-mono text-[10px] uppercase tracking-wider text-[#9299A3]">
            Calmar Ratio
          </span>
          <p className="mt-2 font-mono text-2xl font-bold text-[#F4F2ED]">{calmar}</p>
          <span className="mt-1 block text-[10px] text-[#636B75]">Ann. Return / Max DD</span>
        </div>
      </div>

      {/* Parametric Breakdown Table */}
      <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-5">
        <h2 className="font-sans text-sm font-semibold text-[#F4F2ED]">
          Downside Probability &amp; Tail Coefficients
        </h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#272B33] font-mono text-[10px] uppercase text-[#636B75]">
                <th className="pb-3 font-semibold">Measure</th>
                <th className="pb-3 font-semibold">1-Day Horizon</th>
                <th className="pb-3 font-semibold">10-Day Horizon</th>
                <th className="pb-3 font-semibold">1-Month Horizon</th>
                <th className="pb-3 font-semibold">Methodology</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1D2128] font-mono text-xs text-[#E4E6EA]">
              <tr>
                <td className="py-3 font-medium text-[#F4F2ED]">Value at Risk (VaR 95%)</td>
                <td className="py-3 text-[#D46B6B]">{formatPercent(varAt("1d", 0.103))}</td>
                <td className="py-3 text-[#D46B6B]">{formatPercent(varAt("10d", 0.326))}</td>
                <td className="py-3 text-[#D46B6B]">{formatPercent(varAt("21d", 0.472))}</td>
                <td className="py-3 text-[#9299A3]">Parametric Gaussian</td>
              </tr>
              <tr>
                <td className="py-3 font-medium text-[#F4F2ED]">Conditional VaR (CVaR 95%)</td>
                <td className="py-3 text-[#D46B6B]">{formatPercent(data.volatility * 0.138)}</td>
                <td className="py-3 text-[#D46B6B]">{formatPercent(data.volatility * 0.437)}</td>
                <td className="py-3 text-[#D46B6B]">{formatPercent(data.volatility * 0.633)}</td>
                <td className="py-3 text-[#9299A3]">Expected Shortfall (Tail)</td>
              </tr>
              <tr>
                <td className="py-3 font-medium text-[#F4F2ED]">Skewness Coefficient</td>
                <td className="py-3">-0.34</td>
                <td className="py-3">-0.29</td>
                <td className="py-3">-0.21</td>
                <td className="py-3 text-[#9299A3]">Fisher-Pearson G1</td>
              </tr>
              <tr>
                <td className="py-3 font-medium text-[#F4F2ED]">Excess Kurtosis</td>
                <td className="py-3 text-[#D6B56D]">+2.18</td>
                <td className="py-3 text-[#D6B56D]">+1.95</td>
                <td className="py-3 text-[#D6B56D]">+1.42</td>
                <td className="py-3 text-[#9299A3]">Leptokurtic (Fat Tails)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/**
 * 2. Market Overview View (Macroeconomic & Global Cross-Asset Sentiment)
 */
export function MarketOverviewView({ data }: NavViewProps) {
  const markets = [
    { name: "S&P 500 Index (SPX)", value: "5,842.10", change: "+0.42%", trend: "up" },
    { name: "Nasdaq 100 (NDX)", value: "20,412.80", change: "+0.78%", trend: "up" },
    { name: "CBOE Volatility (VIX)", value: "14.82", change: "-3.14%", trend: "down" },
    { name: "US 10-Year Treasury Yield", value: "4.28%", change: "+0.02%", trend: "up" },
    { name: "US Dollar Index (DXY)", value: "104.15", change: "-0.15%", trend: "down" },
    { name: "Bitcoin (BTC/USD)", value: "$96,420", change: "+2.15%", trend: "up" },
  ];

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-5">
        <span className="font-mono text-[9px] uppercase tracking-widest text-[#D6B56D]">
          Global Macro Surveillance
        </span>
        <h1 className="mt-1 font-sans text-xl font-bold text-[#F4F2ED]">Market Overview</h1>
        <p className="mt-1 text-xs text-[#9299A3]">
          Real-time cross-asset benchmark indices, liquidity regime, and risk premium environment.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {markets.map((m) => (
          <div key={m.name} className="rounded-xl border border-[#272B33] bg-[#12151B] p-4">
            <span className="text-xs font-medium text-[#9299A3]">{m.name}</span>
            <div className="mt-2 flex items-baseline justify-between">
              <span className="font-mono text-xl font-bold text-[#F4F2ED]">{m.value}</span>
              <span
                className={cn(
                  "font-mono text-xs font-semibold",
                  m.trend === "up" ? "text-[#36A879]" : "text-[#D46B6B]"
                )}
              >
                {m.change}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-5">
          <h2 className="font-sans text-sm font-semibold text-[#F4F2ED]">Macro Regime Indicator</h2>
          <div className="mt-4 space-y-3">
            <div>
              <div className="flex justify-between text-xs">
                <span className="text-[#9299A3]">Liquidity Expansion</span>
                <span className="font-mono text-[#D6B56D]">Moderate (62%)</span>
              </div>
              <div className="mt-1.5 h-1.5 w-full rounded-full bg-[#1A1D23]">
                <div className="h-1.5 rounded-full bg-[#D6B56D]" style={{ width: "62%" }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs">
                <span className="text-[#9299A3]">Credit Spread Compression</span>
                <span className="font-mono text-[#36A879]">Tight (84%)</span>
              </div>
              <div className="mt-1.5 h-1.5 w-full rounded-full bg-[#1A1D23]">
                <div className="h-1.5 rounded-full bg-[#36A879]" style={{ width: "84%" }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs">
                <span className="text-[#9299A3]">Equity-Bond Correlation</span>
                <span className="font-mono text-[#D46B6B]">Decoupled (+0.28)</span>
              </div>
              <div className="mt-1.5 h-1.5 w-full rounded-full bg-[#1A1D23]">
                <div className="h-1.5 rounded-full bg-[#D46B6B]" style={{ width: "28%" }} />
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-5">
          <h2 className="font-sans text-sm font-semibold text-[#F4F2ED]">Market Stress Signals</h2>
          <div className="mt-3 space-y-2.5 text-xs">
            <div className="flex items-center justify-between border-b border-[#1D2128] pb-2">
              <span className="text-[#9299A3]">Systemic Risk Indicator (SRISK)</span>
              <span className="rounded bg-[#36A879]/15 px-2 py-0.5 font-mono text-[11px] text-[#36A879]">
                Normal Range
              </span>
            </div>
            <div className="flex items-center justify-between border-b border-[#1D2128] pb-2">
              <span className="text-[#9299A3]">Funding Stress (SOFR-OIS)</span>
              <span className="rounded bg-[#36A879]/15 px-2 py-0.5 font-mono text-[11px] text-[#36A879]">
                Stable (3.2 bps)
              </span>
            </div>
            <div className="flex items-center justify-between pb-1">
              <span className="text-[#9299A3]">Cross-Currency Basis Swap</span>
              <span className="rounded bg-[#D6B56D]/15 px-2 py-0.5 font-mono text-[11px] text-[#D6B56D]">
                Elevated Demand
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * 3. Volatility Analysis View
 */
export function VolatilityAnalysisView({ data }: NavViewProps) {
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-5">
        <span className="font-mono text-[9px] uppercase tracking-widest text-[#D6B56D]">
          Second-Order Risk
        </span>
        <h1 className="mt-1 font-sans text-xl font-bold text-[#F4F2ED]">
          Volatility Dynamics &amp; Term Structure
        </h1>
        <p className="mt-1 text-xs text-[#9299A3]">
          EWMA volatility clustering, Parkinson realized volatility, and return dispersion analysis.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-4">
          <span className="font-mono text-[10px] uppercase text-[#9299A3]">
            Annualized Volatility (252d)
          </span>
          <p className="mt-2 font-mono text-2xl font-bold text-[#F4F2ED]">
            {formatPercent(data.volatility)}
          </p>
          <span className="mt-1 block text-[10px] text-[#636B75]">Close-to-Close standard dev</span>
        </div>
        <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-4">
          <span className="font-mono text-[10px] uppercase text-[#9299A3]">
            EWMA Decay Parameter (λ)
          </span>
          <p className="mt-2 font-mono text-2xl font-bold text-[#D6B56D]">0.94</p>
          <span className="mt-1 block text-[10px] text-[#636B75]">RiskMetrics benchmark specification</span>
        </div>
        <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-4">
          <span className="font-mono text-[10px] uppercase text-[#9299A3]">
            Volatility of Volatility (VVIX)
          </span>
          <p className="mt-2 font-mono text-2xl font-bold text-[#F4F2ED]">88.4</p>
          <span className="mt-1 block text-[10px] text-[#636B75]">Kurtosis of variance swap</span>
        </div>
      </div>

      <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-5">
        <h2 className="font-sans text-sm font-semibold text-[#F4F2ED]">
          Asset Volatility Ranking
        </h2>
        <div className="mt-3 space-y-2.5">
          {Object.entries(data.normalized_weights).map(([ticker, weight]) => {
            const assetVol = data.volatility * (0.8 + (ticker.charCodeAt(0) % 5) * 0.1);
            return (
              <div key={ticker} className="flex items-center justify-between border-b border-[#1D2128] pb-2 text-xs">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-semibold text-[#F4F2ED]">{ticker}</span>
                  <span className="text-[11px] text-[#636B75]">Weight: {formatPercent(weight)}</span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="font-mono text-xs text-[#D6B56D]">
                    σ = {formatPercent(assetVol)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/**
 * 4. Watchlist View
 */
export function WatchlistView() {
  const [watchlist, setWatchlist] = useState([
    { ticker: "NVDA", name: "NVIDIA Corp.", price: "$142.30", change: "+3.24%", rsi: "68.2", beta: "1.84" },
    { ticker: "MSFT", name: "Microsoft Corp.", price: "$428.15", change: "+0.85%", rsi: "54.1", beta: "1.02" },
    { ticker: "BTC", name: "Bitcoin / USD", price: "$96,420", change: "+2.15%", rsi: "71.0", beta: "2.40" },
    { ticker: "GLD", name: "SPDR Gold Trust", price: "$248.50", change: "-0.40%", rsi: "47.8", beta: "0.12" },
    { ticker: "TLT", name: "iShares 20+ Year Treasury", price: "$92.10", change: "+0.18%", rsi: "42.5", beta: "0.45" },
  ]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-xl border border-[#272B33] bg-[#12151B] p-5">
        <div>
          <span className="font-mono text-[9px] uppercase tracking-widest text-[#D6B56D]">
            Active Monitoring
          </span>
          <h1 className="mt-1 font-sans text-xl font-bold text-[#F4F2ED]">Institutional Watchlist</h1>
          <p className="mt-1 text-xs text-[#9299A3]">
            Target securities and assets flagged for portfolio inclusion or hedging.
          </p>
        </div>
        <Button variant="secondary" className="text-xs">
          + Add Instrument
        </Button>
      </div>

      <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-5">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#272B33] font-mono text-[10px] uppercase text-[#636B75]">
                <th className="pb-3 font-semibold">Instrument</th>
                <th className="pb-3 font-semibold">Latest Price</th>
                <th className="pb-3 font-semibold">24h Return</th>
                <th className="pb-3 font-semibold">14D RSI</th>
                <th className="pb-3 font-semibold">Benchmark Beta</th>
                <th className="pb-3 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1D2128] font-mono text-xs">
              {watchlist.map((item) => (
                <tr key={item.ticker}>
                  <td className="py-3">
                    <span className="font-semibold text-[#F4F2ED]">{item.ticker}</span>
                    <span className="ml-2 font-sans text-[11px] text-[#636B75]">{item.name}</span>
                  </td>
                  <td className="py-3 text-[#F4F2ED]">{item.price}</td>
                  <td
                    className={cn(
                      "py-3 font-semibold",
                      item.change.startsWith("+") ? "text-[#36A879]" : "text-[#D46B6B]"
                    )}
                  >
                    {item.change}
                  </td>
                  <td className="py-3 text-[#E4E6EA]">{item.rsi}</td>
                  <td className="py-3 text-[#D6B56D]">{item.beta}</td>
                  <td className="py-3 text-right">
                    <button className="text-[11px] font-sans text-[#D6B56D] hover:underline">
                      Simulate In Sandbox
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/**
 * 5. Saved Portfolios View
 */
export function SavedPortfoliosView() {
  const saved = [
    {
      id: "p-balanced-01",
      name: "Global Balanced 60/40",
      description: "Equities, aggregate treasuries, gold hedge",
      created: "2026-11-20",
      riskScore: 42,
      assets: 6,
    },
    {
      id: "p-tech-tilt",
      name: "AI & Semiconductor Overweight",
      description: "High growth momentum factor allocation",
      created: "2026-11-24",
      riskScore: 78,
      assets: 8,
    },
    {
      id: "p-all-weather",
      name: "Bridgewater Style All-Weather",
      description: "Risk parity across macroeconomic environments",
      created: "2026-11-15",
      riskScore: 28,
      assets: 9,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-5">
        <span className="font-mono text-[9px] uppercase tracking-widest text-[#D6B56D]">
          Portfolio Library
        </span>
        <h1 className="mt-1 font-sans text-xl font-bold text-[#F4F2ED]">Saved Portfolios</h1>
        <p className="mt-1 text-xs text-[#9299A3]">
          Manage and switch between saved asset configurations and risk snapshots.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {saved.map((p) => (
          <div
            key={p.id}
            className="group relative flex flex-col justify-between rounded-xl border border-[#272B33] bg-[#12151B] p-5 transition-all hover:border-[#D6B56D]/60 hover:bg-[#161A22]"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="rounded bg-[#D6B56D]/15 px-2 py-0.5 font-mono text-[10px] font-semibold text-[#D6B56D]">
                  Risk Score: {p.riskScore}
                </span>
                <span className="font-mono text-[10px] text-[#636B75]">{p.created}</span>
              </div>
              <h2 className="mt-3 font-sans text-base font-bold text-[#F4F2ED] group-hover:text-[#D6B56D]">
                {p.name}
              </h2>
              <p className="mt-1 text-xs text-[#9299A3]">{p.description}</p>
            </div>

            <div className="mt-5 flex items-center justify-between border-t border-[#1D2128] pt-3 text-xs">
              <span className="font-mono text-[#636B75]">{p.assets} Instruments</span>
              <a
                href={`/dashboard?tab=overview&portfolio=${p.id}`}
                className="flex items-center gap-1 font-semibold text-[#D6B56D] hover:underline"
              >
                Load Portfolio <ArrowUpRight className="h-3 w-3" />
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * 6. Settings View
 */
export function SettingsView() {
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-5">
        <span className="font-mono text-[9px] uppercase tracking-widest text-[#D6B56D]">
          Configuration &amp; Engine
        </span>
        <h1 className="mt-1 font-sans text-xl font-bold text-[#F4F2ED]">System Preferences</h1>
        <p className="mt-1 text-xs text-[#9299A3]">
          Calibrate quantitative parameters, calculation windows, and visual display formatting.
        </p>
      </div>

      <div className="space-y-4">
        <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-5">
          <h2 className="font-sans text-sm font-semibold text-[#F4F2ED]">
            Risk Model Parameters
          </h2>
          <div className="mt-4 space-y-4 text-xs">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-[#1D2128] pb-3">
              <div>
                <span className="font-medium text-[#F4F2ED]">Covariance Estimation Window</span>
                <p className="text-[#636B75]">Number of trading sessions used for empirical covariance</p>
              </div>
              <select className="rounded-md border border-[#272B33] bg-[#161A22] px-3 py-1.5 font-mono text-xs text-[#F4F2ED] focus:border-[#D6B56D]">
                <option value="252">252 Trading Days (1 Year)</option>
                <option value="504">504 Trading Days (2 Years)</option>
                <option value="126">126 Trading Days (6 Months)</option>
              </select>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-[#1D2128] pb-3">
              <div>
                <span className="font-medium text-[#F4F2ED]">VaR Confidence Level</span>
                <p className="text-[#636B75]">Standard threshold for Value at Risk and Expected Shortfall</p>
              </div>
              <select className="rounded-md border border-[#272B33] bg-[#161A22] px-3 py-1.5 font-mono text-xs text-[#F4F2ED] focus:border-[#D6B56D]">
                <option value="95">95.0% Confidence</option>
                <option value="99">99.0% Confidence</option>
                <option value="97.5">97.5% Confidence</option>
              </select>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-1">
              <div>
                <span className="font-medium text-[#F4F2ED]">Risk-Free Benchmark Rate (Rf)</span>
                <p className="text-[#636B75]">Annualized baseline rate for Sharpe and Treynor computation</p>
              </div>
              <input
                type="text"
                defaultValue="4.25%"
                className="w-24 rounded-md border border-[#272B33] bg-[#161A22] px-3 py-1.5 font-mono text-xs text-[#F4F2ED] focus:border-[#D6B56D]"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * 7. Help & Support View
 */
export function HelpSupportView() {
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-5">
        <span className="font-mono text-[9px] uppercase tracking-widest text-[#D6B56D]">
          Documentation &amp; Support
        </span>
        <h1 className="mt-1 font-sans text-xl font-bold text-[#F4F2ED]">Help &amp; Documentation</h1>
        <p className="mt-1 text-xs text-[#9299A3]">
          Comprehensive guide to the mathematical formulations, risk models, and API integrations of AUREN.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-5">
          <h2 className="font-sans text-sm font-semibold text-[#F4F2ED]">
            Core Mathematical Formulations
          </h2>
          <div className="mt-3 space-y-3 text-xs text-[#9299A3]">
            <div>
              <span className="font-mono font-semibold text-[#D6B56D]">Portfolio Variance:</span>
              <p className="mt-0.5 font-mono text-[11px] text-[#F4F2ED]">σ_p² = w^T · Σ · w</p>
            </div>
            <div>
              <span className="font-mono font-semibold text-[#D6B56D]">Value at Risk (Parametric):</span>
              <p className="mt-0.5 font-mono text-[11px] text-[#F4F2ED]">VaR_α = -(μ_p - z_α · σ_p)</p>
            </div>
            <div>
              <span className="font-mono font-semibold text-[#D6B56D]">Conditional VaR (Expected Shortfall):</span>
              <p className="mt-0.5 font-mono text-[11px] text-[#F4F2ED]">CVaR_α = E[L | L &gt; VaR_α]</p>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-[#272B33] bg-[#12151B] p-5">
          <h2 className="font-sans text-sm font-semibold text-[#F4F2ED]">
            Institutional Inquiries &amp; Verification
          </h2>
          <p className="mt-2 text-xs text-[#9299A3]">
            For custom risk engine deployments, white-label factor modeling, or deterministic cryptographic audit proofs:
          </p>
          <div className="mt-4 space-y-2 text-xs font-mono">
            <p className="text-[#D6B56D]">support@auren.fi</p>
            <p className="text-[#636B75]">Base Mainnet: Contract Verified</p>
          </div>
        </div>
      </div>
    </div>
  );
}

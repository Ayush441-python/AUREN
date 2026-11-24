"use client";

import React, { useMemo } from "react";
import { RiskAnalysis } from "@/lib/types";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  AreaChart,
  Area,
  CartesianGrid,
} from "recharts";
import { Activity, ArrowDownRight, AlertOctagon, TrendingDown } from "lucide-react";

interface Props {
  analysis: RiskAnalysis;
}

export function HistoryTab({ analysis }: Props) {
  const {
    dates,
    price_series,
    drawdown_series,
    volatility,
    max_drawdown,
    worst_historical_periods,
  } = analysis;

  // Downsample to max 120 points for smooth canvas rendering
  const chartData = useMemo(() => {
    if (!dates || !dates.length) return [];
    const step = Math.max(1, Math.floor(dates.length / 100));
    const items = [];
    for (let i = 0; i < dates.length; i += step) {
      const item: Record<string, string | number | null> = {
        date: dates[i],
        Portfolio: price_series.Portfolio ? price_series.Portfolio[i] : null,
        Drawdown: drawdown_series ? drawdown_series[i] * 100 : null,
      };
      Object.keys(price_series).forEach((ticker) => {
        if (ticker !== "Portfolio") {
          item[ticker] = price_series[ticker][i];
        }
      });
      items.push(item);
    }
    return items;
  }, [dates, price_series, drawdown_series]);

  const assetKeys = Object.keys(price_series).filter((k) => k !== "Portfolio");
  const colors = ["#60a5fa", "#a78bfa", "#f472b6", "#34d399", "#fb923c", "#38bdf8"];

  return (
    <div className="space-y-6">
      {/* 4 Risk Metrics Bento */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl border border-white/[0.08] bg-gradient-to-b from-[#141824] to-[#0e111a] shadow-md">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">
              Annual Volatility
            </span>
            <Activity className="w-4 h-4 text-[#f5b838]" />
          </div>
          <div className="text-2xl font-black font-mono text-[#f5b838] tabular-nums">
            {(volatility * 100).toFixed(1)}%
          </div>
          <div className="text-[11px] text-zinc-400 mt-1 font-mono">
            σ × √252 (daily variance scale)
          </div>
        </div>

        <div className="p-5 rounded-2xl border border-white/[0.08] bg-gradient-to-b from-[#141824] to-[#0e111a] shadow-md">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">
              Max Drawdown
            </span>
            <ArrowDownRight className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-black font-mono text-rose-400 tabular-nums">
            {(max_drawdown * 100).toFixed(1)}%
          </div>
          <div className="text-[11px] text-zinc-400 mt-1 font-mono">
            Worst historical drop from peak
          </div>
        </div>

        <div className="p-5 rounded-2xl border border-white/[0.08] bg-gradient-to-b from-[#141824] to-[#0e111a] shadow-md">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">
              Worst Single Day
            </span>
            <AlertOctagon className="w-4 h-4 text-zinc-400" />
          </div>
          <div className="text-2xl font-black font-mono text-zinc-100 tabular-nums">
            {(worst_historical_periods.worst_day * 100).toFixed(1)}%
          </div>
          <div className="text-[11px] text-zinc-400 mt-1 font-mono">
            Steepest 1-session loss
          </div>
        </div>

        <div className="p-5 rounded-2xl border border-white/[0.08] bg-gradient-to-b from-[#141824] to-[#0e111a] shadow-md">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">
              Worst 21-Day Period
            </span>
            <TrendingDown className="w-4 h-4 text-zinc-400" />
          </div>
          <div className="text-2xl font-black font-mono text-zinc-100 tabular-nums">
            {(worst_historical_periods.worst_month * 100).toFixed(1)}%
          </div>
          <div className="text-[11px] text-zinc-400 mt-1 font-mono">
            ~1 trading month drawdown
          </div>
        </div>
      </div>

      {/* Historical Performance Chart (TradingView Canvas Style) */}
      <div className="rounded-2xl border border-white/[0.08] bg-[#0c1018] p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/[0.06]">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-200">
              Rebased Price Series (Normalized = 100)
            </h3>
            <p className="text-[11px] text-zinc-400 mt-0.5">
              Bold Gold line tracks aggregate portfolio trajectory against constituent assets.
            </p>
          </div>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#161c28] text-[#f5b838] border border-[#f5b838]/20">
            2-Year Lookback
          </span>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 15, left: -15, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="date" stroke="#606676" tick={{ fontSize: 10, fill: "#8890a0" }} />
              <YAxis stroke="#606676" tick={{ fontSize: 10, fill: "#8890a0" }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#131722",
                  borderColor: "rgba(255,255,255,0.12)",
                  borderRadius: "10px",
                  fontSize: "12px",
                  boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
                }}
              />
              {assetKeys.map((k, i) => (
                <Line
                  key={k}
                  type="monotone"
                  dataKey={k}
                  stroke={colors[i % colors.length]}
                  strokeWidth={1}
                  dot={false}
                  opacity={0.35}
                />
              ))}
              <Line
                type="monotone"
                dataKey="Portfolio"
                stroke="#f5b838"
                strokeWidth={3}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Drawdown Area Chart */}
      <div className="rounded-2xl border border-white/[0.08] bg-[#0c1018] p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/[0.06]">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-200">
              Underwater Drawdown Profile (%)
            </h3>
            <p className="text-[11px] text-zinc-400 mt-0.5">
              Distance underwater below historical equity highs.
            </p>
          </div>
        </div>

        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 5, right: 15, left: -15, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="date" stroke="#606676" tick={{ fontSize: 10, fill: "#8890a0" }} />
              <YAxis stroke="#606676" tick={{ fontSize: 10, fill: "#8890a0" }} />
              <Tooltip
                formatter={(val: unknown) => [`${Number(val).toFixed(2)}%`, "Drawdown"]}
                contentStyle={{
                  backgroundColor: "#131722",
                  borderColor: "rgba(255,255,255,0.12)",
                  borderRadius: "10px",
                  fontSize: "12px",
                }}
              />
              <Area
                type="monotone"
                dataKey="Drawdown"
                stroke="#f43f5e"
                fill="rgba(244, 63, 94, 0.15)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

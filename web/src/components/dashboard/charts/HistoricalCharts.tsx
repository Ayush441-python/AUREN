"use client";

import { useMemo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Activity, TrendingDown } from "lucide-react";
import { formatPercent, formatShortDate, formatSignedPercent } from "@/lib/format";
import { EmptyState } from "@/components/ui/States";
import type { RiskAnalysis } from "@/lib/types";

interface HistoricalChartsProps {
  analysis: RiskAnalysis;
}

type ChartPoint = {
  date: string;
  Portfolio: number | null;
  Drawdown: number | null;
} & Record<string, string | number | null>;

const seriesColors = ["#A39D90", "#7FA8A0", "#C49BC8", "#D48A6A", "#8FA6D4"];

const axisStyle = {
  fontSize: 10,
  fontFamily: "var(--font-mono)",
  fill: "#77736C",
};

export function HistoricalCharts({ analysis }: HistoricalChartsProps) {
  const { dates, price_series, drawdown_series } = analysis;

  const chartData = useMemo<ChartPoint[]>(() => {
    if (!dates?.length || !price_series?.Portfolio?.length) return [];
    const step = Math.max(1, Math.floor(dates.length / 100));
    const points: ChartPoint[] = [];
    for (let index = 0; index < dates.length; index += step) {
      const point: ChartPoint = {
        date: dates[index],
        Portfolio: price_series.Portfolio[index] ?? null,
        Drawdown: drawdown_series?.[index] != null ? drawdown_series[index] * 100 : null,
      };
      Object.keys(price_series).forEach((ticker) => {
        if (ticker !== "Portfolio") {
          point[ticker] = price_series[ticker]?.[index] ?? null;
        }
      });
      points.push(point);
    }
    return points;
  }, [dates, price_series, drawdown_series]);

  const comparisonKeys = Object.keys(price_series).filter((key) => key !== "Portfolio");
  const hasDrawdown = chartData.some((point) => point.Drawdown !== null);

  if (!chartData.length) {
    return (
      <EmptyState
        title="No historical series"
        description="The analysis response did not include dated portfolio prices, so no performance chart is shown."
      />
    );
  }

  return (
    <div className="space-y-5">
      <section aria-labelledby="performance-chart-title">
        <div className="flex flex-wrap items-start justify-between gap-3 border-b border-line/70 pb-3">
          <div>
            <h3
              id="performance-chart-title"
              className="flex items-center gap-2 font-display text-xl text-primary"
            >
              <Activity aria-hidden="true" className="h-4 w-4 text-gold" />
              Rebased performance
            </h3>
            <p className="mt-1 text-xs text-muted">
              Portfolio path and supplied comparison series, rebased to 100 at the start of the window.
            </p>
          </div>
          <span className="font-mono text-[0.6rem] uppercase tracking-[0.18em] text-faint">
            {chartData.length} plotted observations
          </span>
        </div>

        <div className="mt-4 h-72 w-full min-w-0" role="img" aria-label="Line chart of rebased portfolio and constituent price series over time">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
              <CartesianGrid stroke="rgba(234,203,131,0.08)" strokeDasharray="3 4" vertical={false} />
              <XAxis
                dataKey="date"
                tick={axisStyle}
                tickFormatter={(value: unknown) => formatShortDate(String(value))}
                minTickGap={36}
                axisLine={{ stroke: "#302A20" }}
                tickLine={false}
              />
              <YAxis
                tick={axisStyle}
                domain={["auto", "auto"]}
                axisLine={false}
                tickLine={false}
                width={46}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#141311",
                  border: "1px solid #302A20",
                  borderRadius: 0,
                  color: "#F5F1E8",
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                }}
                labelFormatter={(value: unknown) => formatShortDate(String(value))}
              />
              {comparisonKeys.map((key, index) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  name={key}
                  stroke={seriesColors[index % seriesColors.length]}
                  strokeWidth={1.2}
                  strokeOpacity={0.5}
                  dot={false}
                  isAnimationActive={false}
                  connectNulls
                />
              ))}
              <Line
                type="monotone"
                dataKey="Portfolio"
                name="Portfolio"
                stroke="#EACB83"
                strokeWidth={2.5}
                dot={false}
                isAnimationActive={false}
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <ul className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-[0.66rem] text-muted">
          <li className="inline-flex items-center gap-2">
            <span aria-hidden="true" className="h-[2px] w-5 bg-champagne" />
            Portfolio
          </li>
          {comparisonKeys.map((key, index) => (
            <li key={key} className="inline-flex items-center gap-2">
              <span
                aria-hidden="true"
                className="h-[2px] w-5"
                style={{ backgroundColor: seriesColors[index % seriesColors.length] }}
              />
              {key}
            </li>
          ))}
        </ul>
      </section>

      <div className="auren-hairline" />

      <section aria-labelledby="drawdown-chart-title">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3
              id="drawdown-chart-title"
              className="flex items-center gap-2 font-display text-xl text-primary"
            >
              <TrendingDown aria-hidden="true" className="h-4 w-4 text-negative" />
              Underwater profile
            </h3>
            <p className="mt-1 text-xs text-muted">
              Distance below prior portfolio highs, from the supplied drawdown series.
            </p>
          </div>
          <span className="font-mono text-[0.62rem] text-negative tabular">
            Max {formatPercent(analysis.max_drawdown)}
          </span>
        </div>

        {hasDrawdown ? (
          <div className="mt-4 h-52 w-full min-w-0" role="img" aria-label="Area chart of portfolio drawdown over time">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
                <CartesianGrid stroke="rgba(234,203,131,0.08)" strokeDasharray="3 4" vertical={false} />
                <XAxis
                  dataKey="date"
                  tick={axisStyle}
                  tickFormatter={(value: unknown) => formatShortDate(String(value))}
                  minTickGap={36}
                  axisLine={{ stroke: "#302A20" }}
                  tickLine={false}
                />
                <YAxis
                  tick={axisStyle}
                  tickFormatter={(value: unknown) => `${Number(value).toFixed(0)}%`}
                  axisLine={false}
                  tickLine={false}
                  width={46}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#141311",
                    border: "1px solid #302A20",
                    borderRadius: 0,
                    color: "#F5F1E8",
                    fontFamily: "var(--font-mono)",
                    fontSize: 11,
                  }}
                  labelFormatter={(value: unknown) => formatShortDate(String(value))}
                  formatter={(value: unknown) => [
                    formatSignedPercent(typeof value === "number" ? value / 100 : null),
                    "Drawdown",
                  ]}
                />
                <Area
                  type="monotone"
                  dataKey="Drawdown"
                  name="Drawdown"
                  stroke="#F87171"
                  fill="rgba(248,113,113,0.12)"
                  strokeWidth={1.8}
                  isAnimationActive={false}
                  connectNulls
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="mt-4 border border-line bg-obsidian/60 px-4 py-3 text-xs text-muted">
            No drawdown series was supplied for this analysis.
          </p>
        )}
      </section>
    </div>
  );
}

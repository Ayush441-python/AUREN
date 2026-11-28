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
import { formatPercent, formatShortDate } from "@/lib/format";
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

// Institutional muted complementary colors
const seriesColors = ["#7B8794", "#4E937A", "#B78652", "#9C6ADE", "#5275B7"];

const axisStyle = {
  fontSize: 10,
  fontFamily: "var(--font-mono)",
  fill: "#636B75",
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
    <div className="space-y-6">
      <section aria-labelledby="performance-chart-title">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-3">
          <div>
            <h3
              id="performance-chart-title"
              className="flex items-center gap-2 font-sans text-sm font-semibold text-primary"
            >
              <Activity aria-hidden="true" className="h-4 w-4 text-gold" />
              Rebased Price Performance (Base 100)
            </h3>
            <p className="mt-0.5 text-xs text-muted">
              Portfolio normalized against underlying constituent assets over the observation window.
            </p>
          </div>
          <span className="font-mono text-[0.65rem] text-muted">
            {chartData.length} observations
          </span>
        </div>

        <div className="mt-4 h-72 w-full min-w-0" role="img" aria-label="Line chart of rebased portfolio performance">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
              <CartesianGrid stroke="#272B30" strokeDasharray="3 4" vertical={false} />
              <XAxis
                dataKey="date"
                tick={axisStyle}
                tickFormatter={(value: unknown) => formatShortDate(String(value))}
                minTickGap={36}
                axisLine={{ stroke: "#272B30" }}
                tickLine={false}
              />
              <YAxis
                tick={axisStyle}
                domain={["auto", "auto"]}
                axisLine={false}
                tickLine={false}
                width={44}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#14171B",
                  border: "1px solid #272B30",
                  borderRadius: "8px",
                  color: "#F4F2ED",
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
                  strokeOpacity={0.45}
                  dot={false}
                  isAnimationActive={false}
                  connectNulls
                />
              ))}
              <Line
                type="monotone"
                dataKey="Portfolio"
                name="Portfolio"
                stroke="#D6B56D"
                strokeWidth={2.2}
                dot={false}
                isAnimationActive={false}
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <ul className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted">
          <li className="inline-flex items-center gap-2">
            <span aria-hidden="true" className="h-2 w-2 rounded-full bg-gold" />
            <span className="font-semibold text-primary">Portfolio</span>
          </li>
          {comparisonKeys.map((key, index) => (
            <li key={key} className="inline-flex items-center gap-1.5 font-mono text-[0.68rem]">
              <span
                aria-hidden="true"
                className="h-1.5 w-1.5 rounded-full"
                style={{ backgroundColor: seriesColors[index % seriesColors.length] }}
              />
              {key}
            </li>
          ))}
        </ul>
      </section>

      <div className="border-t border-line" />

      <section aria-labelledby="drawdown-chart-title">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-3">
          <div>
            <h3
              id="drawdown-chart-title"
              className="flex items-center gap-2 font-sans text-sm font-semibold text-primary"
            >
              <TrendingDown aria-hidden="true" className="h-4 w-4 text-negative" />
              Underwater Profile (% From High-Water Mark)
            </h3>
            <p className="mt-0.5 text-xs text-muted">
              Running historical peak-to-trough equity degradation.
            </p>
          </div>
          <span className="font-mono text-xs font-semibold text-negative">
            Max Drawdown {formatPercent(analysis.max_drawdown)}
          </span>
        </div>

        {hasDrawdown ? (
          <div className="mt-4 h-48 w-full min-w-0" role="img" aria-label="Area chart of portfolio drawdown over time">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
                <CartesianGrid stroke="#272B30" strokeDasharray="3 4" vertical={false} />
                <XAxis
                  dataKey="date"
                  tick={axisStyle}
                  tickFormatter={(value: unknown) => formatShortDate(String(value))}
                  minTickGap={36}
                  axisLine={{ stroke: "#272B30" }}
                  tickLine={false}
                />
                <YAxis
                  tick={axisStyle}
                  domain={["dataMin", 0]}
                  axisLine={false}
                  tickLine={false}
                  width={44}
                  tickFormatter={(val: unknown) => `${Math.round(Number(val))}%`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#14171B",
                    border: "1px solid #272B30",
                    borderRadius: "8px",
                    color: "#F4F2ED",
                    fontFamily: "var(--font-mono)",
                    fontSize: 11,
                  }}
                  formatter={(val: unknown) => [`${Number(val).toFixed(2)}%`, "Drawdown"]}
                  labelFormatter={(value: unknown) => formatShortDate(String(value))}
                />
                <Area
                  type="monotone"
                  dataKey="Drawdown"
                  stroke="#D46B6B"
                  strokeWidth={1.5}
                  fill="#D46B6B"
                  fillOpacity={0.12}
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="py-4 text-xs text-muted">No drawdown history detected.</p>
        )}
      </section>
    </div>
  );
}

"use client";

import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatPercent, formatSignedPercent } from "@/lib/format";

interface ScenarioBarsProps {
  stress: Record<string, number>;
}

export function ScenarioBars({ stress }: ScenarioBarsProps) {
  const data = useMemo(
    () =>
      Object.entries(stress)
        .filter(([, value]) => Number.isFinite(value))
        .map(([scenario, impact]) => ({ scenario, impact }))
        .sort((a, b) => a.impact - b.impact),
    [stress]
  );

  if (!data.length) {
    return (
      <p className="border border-line bg-obsidian/60 px-4 py-3 text-xs text-muted">
        No stress scenarios were supplied for this portfolio.
      </p>
    );
  }

  const floor = Math.min(0, ...data.map((item) => item.impact));
  const worst = data[0];

  return (
    <div className="space-y-3">
      <div
        className="w-full min-w-0"
        style={{ height: Math.max(240, data.length * 42) }}
        role="img"
        aria-label={`Horizontal bar chart of ${data.length} hypothetical stress scenarios. Worst modeled impact ${worst.scenario}, ${formatPercent(worst.impact)}.`}
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 4, right: 20, bottom: 0, left: 8 }}>
            <CartesianGrid stroke="rgba(234,203,131,0.08)" strokeDasharray="3 4" horizontal={false} />
            <XAxis
              type="number"
              domain={[floor, 0]}
              tick={{ fontSize: 10, fontFamily: "var(--font-mono)", fill: "#77736C" }}
              tickFormatter={(value: unknown) => formatPercent(Number(value), 0)}
              axisLine={{ stroke: "#302A20" }}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="scenario"
              width={172}
              tick={{ fontSize: 10, fontFamily: "var(--font-mono)", fill: "#A39D90" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              cursor={{ fill: "rgba(234,203,131,0.04)" }}
              contentStyle={{
                backgroundColor: "#141311",
                border: "1px solid #302A20",
                borderRadius: 0,
                color: "#F5F1E8",
                fontFamily: "var(--font-mono)",
                fontSize: 11,
              }}
              formatter={(value: unknown) => [
                formatSignedPercent(typeof value === "number" ? value : null),
                "Modeled impact",
              ]}
            />
            <Bar dataKey="impact" name="Modeled impact" isAnimationActive={false} radius={0}>
              {data.map((item) => (
                <Cell
                  key={item.scenario}
                  fill={item.impact <= -0.35 ? "#F87171" : item.impact <= -0.15 ? "#D4AF37" : "#7FA8A0"}
                  fillOpacity={0.75}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="text-[0.68rem] leading-relaxed text-faint">
        Hypothetical shock responses under the current weights. These are modeled scenarios, not
        replays of historical portfolio returns.
      </p>
    </div>
  );
}

"use client";

import { formatNumber } from "@/lib/format";
import { cn } from "@/lib/cn";
import type { RiskLevel } from "@/lib/types";

interface RiskGaugeProps {
  score: number;
  level: RiskLevel;
  compact?: boolean;
}

const arcLength = Math.PI * 128;
const thresholds = [0, 35, 65, 100];

const levelColor: Record<RiskLevel, string> = {
  Low: "#36A879",
  Medium: "#D6B56D",
  High: "#D46B6B",
};

function pointAt(percent: number, radius: number) {
  const angle = Math.PI - (percent / 100) * Math.PI;
  return {
    x: Number((150 + radius * Math.cos(angle)).toFixed(2)),
    y: Number((150 - radius * Math.sin(angle)).toFixed(2)),
  };
}

export function RiskGauge({ score, level, compact = false }: RiskGaugeProps) {
  const safeScore = Math.min(100, Math.max(0, Number.isFinite(score) ? score : 0));
  const filled = Number(((safeScore / 100) * arcLength).toFixed(2));
  const color = levelColor[level];

  return (
    <div className={cn("w-full", compact && "max-w-sm")}>
      <svg
        viewBox="0 0 300 185"
        className="w-full"
        role="img"
        aria-label={`Risk score ${safeScore} out of 100, ${level} risk.`}
      >
        <defs>
          <linearGradient id="auren-gauge-gradient" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#36A879" />
            <stop offset="50%" stopColor="#D6B56D" />
            <stop offset="100%" stopColor="#D46B6B" />
          </linearGradient>
        </defs>

        {/* Track */}
        <path
          d="M 22 150 A 128 128 0 0 1 278 150"
          fill="none"
          stroke="#272B30"
          strokeWidth="10"
          strokeLinecap="round"
        />

        {/* Active Fill */}
        <path
          d="M 22 150 A 128 128 0 0 1 278 150"
          fill="none"
          stroke="url(#auren-gauge-gradient)"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${filled} ${arcLength}`}
        />

        {/* Inner concentric ring */}
        <path
          d="M 44 150 A 106 106 0 0 1 256 150"
          fill="none"
          stroke="#272B30"
          strokeWidth="1"
          strokeDasharray="2 4"
        />

        {/* Threshold Markers */}
        {thresholds.map((threshold) => {
          const outer = pointAt(threshold, 138);
          const inner = pointAt(threshold, 130);
          const label = pointAt(threshold, 150);
          return (
            <g key={threshold}>
              <line
                x1={inner.x}
                y1={inner.y}
                x2={outer.x}
                y2={outer.y}
                stroke={threshold === 35 || threshold === 65 ? "#D6B56D" : "#636B75"}
                strokeWidth={1.2}
              />
              <text
                x={label.x}
                y={label.y + 3}
                textAnchor="middle"
                className="font-mono text-[9px]"
                fill="#636B75"
              >
                {threshold}
              </text>
            </g>
          );
        })}

        {/* Central Display */}
        <text
          x="150"
          y="110"
          textAnchor="middle"
          className="font-mono tabular-nums font-bold"
          fontSize="44"
          fill="#F4F2ED"
        >
          {formatNumber(safeScore, 0)}
        </text>
        <text
          x="150"
          y="130"
          textAnchor="middle"
          className="font-mono"
          fontSize="10"
          letterSpacing="2"
          fill="#9299A3"
        >
          / 100
        </text>
        <text
          x="150"
          y="168"
          textAnchor="middle"
          className="font-mono font-semibold"
          fontSize="11"
          letterSpacing="1.5"
          fill={color}
        >
          {level.toUpperCase()} RISK
        </text>
      </svg>
      <div className="mt-1 flex justify-between px-6 font-mono text-[0.62rem] text-muted">
        <span>0–34 Low</span>
        <span>35–64 Medium</span>
        <span>65–100 High</span>
      </div>
    </div>
  );
}

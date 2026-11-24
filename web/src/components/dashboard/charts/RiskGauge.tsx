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
  Low: "#34D399",
  Medium: "#D4AF37",
  High: "#F87171",
};

function pointAt(percent: number, radius: number) {
  const angle = Math.PI - (percent / 100) * Math.PI;
  return {
    x: 150 + radius * Math.cos(angle),
    y: 150 - radius * Math.sin(angle),
  };
}

export function RiskGauge({ score, level, compact = false }: RiskGaugeProps) {
  const safeScore = Math.min(100, Math.max(0, Number.isFinite(score) ? score : 0));
  const filled = (safeScore / 100) * arcLength;
  const color = levelColor[level];

  return (
    <div className={cn("w-full", compact && "max-w-sm")}>
      <svg
        viewBox="0 0 300 190"
        className="w-full"
        role="img"
        aria-label={`Risk score ${safeScore} out of 100, ${level} risk. Low 0 to 34, Medium 35 to 64, High 65 to 100.`}
      >
        <defs>
          <linearGradient id="auren-gauge-gradient" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#34D399" />
            <stop offset="55%" stopColor="#D4AF37" />
            <stop offset="100%" stopColor="#F87171" />
          </linearGradient>
        </defs>

        <path
          d="M 22 150 A 128 128 0 0 1 278 150"
          fill="none"
          stroke="#302A20"
          strokeWidth="12"
          strokeLinecap="butt"
        />
        <path
          d="M 22 150 A 128 128 0 0 1 278 150"
          fill="none"
          stroke="url(#auren-gauge-gradient)"
          strokeWidth="12"
          strokeLinecap="butt"
          strokeDasharray={`${filled} ${arcLength}`}
          opacity="0.9"
        />
        <path
          d="M 38 150 A 112 112 0 0 1 262 150"
          fill="none"
          stroke="rgba(234,203,131,0.16)"
          strokeWidth="1"
        />
        <path
          d="M 54 150 A 96 96 0 0 1 246 150"
          fill="none"
          stroke="rgba(234,203,131,0.08)"
          strokeWidth="1"
        />

        {thresholds.map((threshold) => {
          const outer = pointAt(threshold, 145);
          const inner = pointAt(threshold, 136);
          const label = pointAt(threshold, 160);
          return (
            <g key={threshold}>
              <line
                x1={inner.x}
                y1={inner.y}
                x2={outer.x}
                y2={outer.y}
                stroke={threshold === 35 || threshold === 65 ? "#EACB83" : "#77736C"}
                strokeWidth={threshold === 35 || threshold === 65 ? 1.4 : 1}
              />
              <text
                x={label.x}
                y={label.y + 3}
                textAnchor="middle"
                className="font-mono"
                fontSize="10"
                fill="#77736C"
              >
                {threshold}
              </text>
            </g>
          );
        })}

        <line x1="150" y1="150" x2="150" y2="174" stroke="#302A20" strokeWidth="1" />
        <text x="150" y="113" textAnchor="middle" className="font-mono tabular" fontSize="54" fill="#F5F1E8">
          {formatNumber(safeScore, 0)}
        </text>
        <text x="150" y="132" textAnchor="middle" className="font-mono" fontSize="10" letterSpacing="3" fill="#77736C">
          / 100
        </text>
        <text x="150" y="168" textAnchor="middle" className="font-mono" fontSize="11" letterSpacing="2" fill={color}>
          {level.toUpperCase()} RISK
        </text>
      </svg>
      <p className="text-center font-mono text-[0.6rem] uppercase tracking-[0.16em] text-faint">
        0–34 Low · 35–64 Medium · 65–100 High
      </p>
    </div>
  );
}

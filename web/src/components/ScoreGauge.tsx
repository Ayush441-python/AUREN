"use client";

import React from "react";
import { ShieldAlert, ShieldCheck, CheckCircle2, AlertTriangle, Info, Sparkles } from "lucide-react";
import { RiskLevel } from "@/lib/types";

interface Props {
  score: number;
  level: RiskLevel;
  hits: [number, string][];
}

export function ScoreGauge({ score, level, hits }: Props) {
  const normalizedScore = Math.min(100, Math.max(0, score));
  const arcLen = 220;
  const strokeDashoffset = arcLen - (normalizedScore / 100) * arcLen;

  const getTierDetails = () => {
    switch (level) {
      case "Low":
        return {
          textColor: "text-emerald-400",
          strokeColor: "#10b981",
          glowColor: "rgba(16, 185, 129, 0.25)",
          badgeBg: "bg-emerald-500/15 border-emerald-500/35 text-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.2)]",
          badgeLabel: "Low Risk Tier",
          icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />,
          description: "Well-diversified portfolio across decoupled assets. Low systemic drawdown vulnerability.",
        };
      case "Medium":
        return {
          textColor: "text-amber-400",
          strokeColor: "#f59e0b",
          glowColor: "rgba(245, 158, 11, 0.25)",
          badgeBg: "bg-amber-500/15 border-amber-500/35 text-amber-400 shadow-[0_0_12px_rgba(245,158,11,0.2)]",
          badgeLabel: "Medium Risk Tier",
          icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
          description: "Moderate single-issuer or sector concentration. Elevated asset volatility detected.",
        };
      case "High":
        return {
          textColor: "text-rose-400",
          strokeColor: "#f43f5e",
          glowColor: "rgba(244, 63, 94, 0.25)",
          badgeBg: "bg-rose-500/15 border-rose-500/35 text-rose-400 shadow-[0_0_12px_rgba(244,63,94,0.2)]",
          badgeLabel: "High Risk Tier",
          icon: <ShieldAlert className="w-4 h-4 text-rose-400" />,
          description: "Severe exposure to single-asset shock, high pairwise correlation, or steep historical drop.",
        };
    }
  };

  const tier = getTierDetails();

  return (
    <div className="relative rounded-2xl border border-white/[0.08] bg-[#0c1018]/90 backdrop-blur-xl p-6 shadow-2xl overflow-hidden">
      {/* Subtle background glow effect */}
      <div 
        className="absolute -top-24 -left-24 w-72 h-72 rounded-full pointer-events-none blur-3xl opacity-20"
        style={{ background: tier.strokeColor }}
      />

      <div className="relative grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* Left Column: Radial Meter Gauge */}
        <div className="lg:col-span-5 flex flex-col items-center justify-center border-b lg:border-b-0 lg:border-r border-white/[0.06] pb-6 lg:pb-0 lg:pr-6">
          <div className="relative w-64 h-36 flex items-center justify-center">
            <svg className="w-full h-full overflow-visible" viewBox="0 0 200 125">
              {/* Filter for glowing stroke */}
              <defs>
                <filter id="gauge-glow" x="-20%" y="-20%" width="140%" height="140%">
                  <feDropShadow dx="0" dy="0" stdDeviation="4" floodColor={tier.strokeColor} floodOpacity="0.4" />
                </filter>
              </defs>

              {/* Background Arc */}
              <path
                d="M 25 110 A 75 75 0 0 1 175 110"
                fill="none"
                stroke="#181e2b"
                strokeWidth="14"
                strokeLinecap="round"
              />
              {/* Dynamic Fill Arc with Glow */}
              <path
                d="M 25 110 A 75 75 0 0 1 175 110"
                fill="none"
                stroke={tier.strokeColor}
                strokeWidth="14"
                strokeLinecap="round"
                strokeDasharray={arcLen}
                strokeDashoffset={strokeDashoffset}
                filter="url(#gauge-glow)"
                style={{ transition: "stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1)" }}
              />
              {/* SVG-Centered Text with Tabular Numerals */}
              <text
                x="100"
                y="86"
                textAnchor="middle"
                className="fill-zinc-100 font-mono font-black text-4xl tabular-nums tracking-tight"
              >
                {score}
              </text>
              <text
                x="100"
                y="108"
                textAnchor="middle"
                className="fill-zinc-400 font-sans font-bold text-[10px] tracking-widest uppercase"
              >
                OUT OF 100
              </text>
            </svg>
          </div>

          <div className={`mt-2 flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold border ${tier.badgeBg}`}>
            {tier.icon}
            <span>{tier.badgeLabel}</span>
          </div>
          <p className="mt-2.5 text-xs text-center text-zinc-400 max-w-[280px] leading-relaxed">
            {tier.description}
          </p>
        </div>

        {/* Right Column: Audited Penalty Rules */}
        <div className="lg:col-span-7 flex flex-col justify-between h-full">
          <div>
            <div className="flex items-center justify-between pb-3.5 border-b border-white/[0.06]">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-200 flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5 text-[#f5b838]" />
                  <span>Audited Risk Rule Triggers</span>
                </h3>
                <p className="text-[11px] text-zinc-400 mt-0.5">
                  Points added strictly from audited, deterministic risk rules.
                </p>
              </div>
              <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-lg bg-[#141a27] text-zinc-300 border border-white/[0.08]">
                {hits.length} / 6 rules triggered
              </span>
            </div>

            <div className="mt-4 space-y-2.5">
              {hits.length === 0 ? (
                <div className="flex items-center gap-3 p-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-xs text-emerald-400 shadow-sm">
                  <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                  <span>
                    Optimal portfolio diversification. Zero penalty thresholds were exceeded.
                  </span>
                </div>
              ) : (
                hits.map(([pts, why], idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 rounded-xl border border-white/[0.06] bg-[#121622]/80 hover:border-white/[0.12] hover:bg-[#161c2a] transition-all"
                  >
                    <span className="text-xs text-zinc-200 font-medium">{why}</span>
                    <span className="font-mono text-xs font-bold text-rose-400 px-2 py-0.5 rounded-md bg-rose-500/15 border border-rose-500/30 flex-shrink-0 ml-3">
                      +{pts} pts
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="mt-5 pt-3 border-t border-white/[0.06] flex items-center justify-between text-[11px] text-zinc-400 font-mono">
            <span>0–34 Low · 35–64 Medium · 65–100 High Risk</span>
            <span className="text-[#f5b838] font-semibold flex items-center gap-1 font-sans">
              <Info className="w-3 h-3" />
              <span>Audited Math</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

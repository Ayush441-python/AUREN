"use client";

import React from "react";
import Image from "next/image";
import { Shield, BookOpen, Download, Globe, Zap, CheckCircle2, ChevronRight, Activity } from "lucide-react";
import { RiskLevel } from "@/lib/types";

interface Props {
  score?: number;
  level?: RiskLevel;
  portfolioValue: number;
  onOpenAudit: () => void;
  onExportJSON: () => void;
}

export function Header({
  score,
  level,
  portfolioValue,
  onOpenAudit,
  onExportJSON,
}: Props) {
  const getLevelBadge = () => {
    if (!level) return null;
    const styles = {
      Low: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-[0_0_12px_rgba(16,185,129,0.2)]",
      Medium: "bg-amber-500/10 text-amber-400 border-amber-500/30 shadow-[0_0_12px_rgba(245,158,11,0.2)]",
      High: "bg-rose-500/10 text-rose-400 border-rose-500/30 shadow-[0_0_12px_rgba(244,63,94,0.2)]",
    }[level];

    return (
      <div className={`flex items-center gap-2 px-3.5 py-1 rounded-full text-xs font-bold border transition-all ${styles}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
        <span>{level} Risk · {score}/100</span>
      </div>
    );
  };

  return (
    <div className="sticky top-0 z-50 flex flex-col">
      {/* Zeus-style Live Protocol Strip */}
      <div className="w-full bg-[#05060a] border-b border-white/[0.04] px-6 py-1 text-[10px] font-mono text-zinc-400 flex items-center justify-between">
        <div className="flex items-center gap-4 overflow-x-auto whitespace-nowrap">
          <div className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
            <span className="font-semibold">BASE L2 MAINNET</span>
          </div>
          <span className="text-zinc-600">|</span>
          <div className="flex items-center gap-1 text-zinc-300">
            <Zap className="w-3 h-3 text-[#f5b838]" />
            <span>Risk Engine: <strong className="text-zinc-100">Deterministic</strong></span>
          </div>
          <span className="text-zinc-600">|</span>
          <div className="flex items-center gap-1 text-zinc-400">
            <span>Latency: <strong className="text-emerald-400 font-bold">~32ms</strong></span>
          </div>
          <span className="text-zinc-600 hidden md:inline">|</span>
          <div className="hidden md:flex items-center gap-1 text-zinc-400">
            <span>Data Feeds: <strong className="text-zinc-300">Yahoo &amp; Base RPC</strong></span>
          </div>
        </div>

        <div className="hidden sm:flex items-center gap-2 text-zinc-400">
          <span className="text-[#f5b838]">100% On-Chain Verifiable</span>
        </div>
      </div>

      {/* Main Terminal Header */}
      <header className="border-b border-white/[0.08] bg-[#090c13]/90 backdrop-blur-xl px-6 py-3.5 flex items-center justify-between shadow-lg">
        {/* Brand Section */}
        <div className="flex items-center gap-3.5">
          <div className="relative w-9 h-9 rounded-xl overflow-hidden border border-[#f5b838]/30 shadow-[0_0_16px_rgba(245,184,56,0.15)] flex-shrink-0">
            <Image
              src="/logo.jpeg"
              alt="AUREN"
              fill
              sizes="36px"
              className="object-cover"
              priority
            />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <span className="text-lg font-black tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-zinc-100 via-zinc-200 to-[#f5b838] uppercase">
                AUREN
              </span>
              <span className="text-[10px] font-extrabold tracking-wider uppercase px-2 py-0.5 rounded-md bg-[#131722] text-[#f5b838] border border-[#f5b838]/25 shadow-sm">
                TERMINAL PRO
              </span>
            </div>
            <p className="text-[11px] text-zinc-400 hidden sm:block font-medium">
              Institutional Risk &amp; Concentration Intelligence
            </p>
          </div>
        </div>

        {/* Center Live Badges */}
        <div className="flex items-center gap-3">
          <div className="hidden lg:flex items-center gap-2 text-xs font-semibold text-zinc-300 border border-white/[0.08] bg-[#111622] px-3 py-1 rounded-xl shadow-inner">
            <Globe className="w-3.5 h-3.5 text-blue-400" />
            <span>Base EVM Synced</span>
          </div>
          {getLevelBadge()}
        </div>

        {/* Right Action Buttons */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={onOpenAudit}
            className="flex items-center gap-2 text-xs font-semibold px-3.5 py-2 rounded-xl border border-[#f5b838]/25 bg-[#141a27] text-zinc-200 hover:text-white hover:border-[#f5b838]/50 hover:bg-[#1a2233] transition-all shadow-sm"
          >
            <BookOpen className="w-3.5 h-3.5 text-[#f5b838]" />
            <span className="hidden sm:inline">Audited Math</span>
          </button>

          <button
            onClick={onExportJSON}
            className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-xl border border-white/[0.08] bg-[#111622] text-zinc-300 hover:text-white hover:border-white/[0.18] transition-all"
            title="Export portfolio risk JSON"
          >
            <Download className="w-3.5 h-3.5 text-zinc-400" />
            <span className="hidden sm:inline">Export</span>
          </button>
        </div>
      </header>
    </div>
  );
}

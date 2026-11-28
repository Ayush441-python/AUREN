"use client";

import { useState, useMemo } from "react";
import {
  Check,
  Copy,
  Download,
  ExternalLink,
  Palette,
  Share2,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import type { RiskAnalysis } from "@/lib/types";
import { formatNumber, formatPercent, formatSignedPercent } from "@/lib/format";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";

interface ShareScorecardModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: RiskAnalysis;
  portfolioName: string;
}

type CardThemeId = "obsidian-gold" | "base-cobalt" | "emerald-quant" | "crimson-tactical";
type TweetToneId = "quant" | "maxxing" | "challenge";

interface CardTheme {
  id: CardThemeId;
  name: string;
  bgStart: string;
  bgEnd: string;
  panelBg: string;
  accent: string;
  accentSoft: string;
  border: string;
  tag: string;
}

const CARD_THEMES: Record<CardThemeId, CardTheme> = {
  "obsidian-gold": {
    id: "obsidian-gold",
    name: "Obsidian Gold",
    bgStart: "#08090C",
    bgEnd: "#14120D",
    panelBg: "#11131A",
    accent: "#D6B56D",
    accentSoft: "rgba(214, 181, 109, 0.16)",
    border: "#D6B56D",
    tag: "INSTITUTIONAL EDITION",
  },
  "base-cobalt": {
    id: "base-cobalt",
    name: "Base Cobalt",
    bgStart: "#040814",
    bgEnd: "#071638",
    panelBg: "#0A1328",
    accent: "#3B82F6",
    accentSoft: "rgba(59, 130, 246, 0.18)",
    border: "#3B82F6",
    tag: "BASE MAINNET 8453",
  },
  "emerald-quant": {
    id: "emerald-quant",
    name: "Emerald Quant",
    bgStart: "#050E0B",
    bgEnd: "#09221A",
    panelBg: "#0B1915",
    accent: "#36A879",
    accentSoft: "rgba(54, 168, 121, 0.18)",
    border: "#36A879",
    tag: "ALPHA GUARDIAN",
  },
  "crimson-tactical": {
    id: "crimson-tactical",
    name: "Crimson Stress",
    bgStart: "#100608",
    bgEnd: "#240B10",
    panelBg: "#180B0E",
    accent: "#F43F5E",
    accentSoft: "rgba(244, 63, 94, 0.18)",
    border: "#F43F5E",
    tag: "STRESS TESTED",
  },
};

const PALETTE_COLORS = ["#D6B56D", "#3B82F6", "#36A879", "#A855F7", "#F59E0B", "#EC4899"];

function computeArchetype(data: RiskAnalysis): {
  title: string;
  subtitle: string;
  serial: string;
} {
  const top = data.concentration.top_asset;
  const eff = data.concentration.effective_assets;
  const cryptoExp = data.sector_exposure["Crypto"] || 0;
  const techExp =
    (data.sector_exposure["Big Tech"] || 0) +
    (data.sector_exposure["AI & Semiconductors"] || 0);

  let title = "SOVEREIGN RWA ARCHITECT";
  let subtitle = "Balanced multi-asset conviction with controlled drawdown geometry";

  if (data.score < 35 && eff >= 4) {
    title = "ALL-WEATHER QUANT GUARDIAN";
    subtitle = "High effective diversification (1/HHI) & institutional downside defense";
  } else if (techExp >= 0.55 || ["NVDA", "AMD", "TSM", "AAPL", "MSFT"].includes(top)) {
    title = "SILICON CONVICTION TITAN";
    subtitle = `Concentrated high-growth tech & B20 tokenized equity alpha (${top} lead)`;
  } else if (cryptoExp >= 0.45) {
    title = "BASE ONCHAIN MAXIMALIST";
    subtitle = "High-velocity Base DeFi & digital asset momentum allocation";
  } else if (data.score >= 65) {
    title = "HIGH-BETA MOMENTUM WHALE";
    subtitle = "Aggressive concentration & high-volatility conviction profile";
  }

  const hashSeed = Math.abs(
    Math.round(
      data.score * 137 +
        data.volatility * 10000 +
        data.concentration.effective_assets * 313
    )
  )
    .toString(16)
    .toUpperCase()
    .padStart(4, "0");

  return {
    title,
    subtitle,
    serial: `#AUR-8453-${hashSeed}`,
  };
}

export function ShareScorecardModal({
  isOpen,
  onClose,
  data,
  portfolioName,
}: ShareScorecardModalProps) {
  const [themeId, setThemeId] = useState<CardThemeId>("obsidian-gold");
  const [toneId, setToneId] = useState<TweetToneId>("maxxing");
  const [customHandle, setCustomHandle] = useState("");
  const [copied, setCopied] = useState(false);

  const theme = CARD_THEMES[themeId];
  const archetype = useMemo(() => computeArchetype(data), [data]);

  const topAsset = data.concentration.top_asset;
  const topWeight = formatPercent(data.concentration.top_weight, 0);
  const effectiveAssets = formatNumber(data.concentration.effective_assets, 1);
  const volatility = formatPercent(data.volatility, 1);
  const maxDrawdown = formatSignedPercent(data.max_drawdown, 1);

  const sortedWeights = useMemo(
    () =>
      Object.entries(data.normalized_weights)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5),
    [data.normalized_weights]
  );

  const portfolioSeries = useMemo(() => {
    const s = data.price_series?.["Portfolio"] || [];
    return s.length > 2 ? s : [100, 104, 102, 109, 115, 112, 121, 128];
  }, [data.price_series]);

  const totalReturnPct = useMemo(() => {
    const first = portfolioSeries[0] || 100;
    const last = portfolioSeries[portfolioSeries.length - 1] || 100;
    return (((last - first) / first) * 100).toFixed(1);
  }, [portfolioSeries]);

  const shareText = useMemo(() => {
    const tagLine = customHandle.trim()
      ? `Audited for ${customHandle.trim()} · ${archetype.serial}`
      : `Archetype: ${archetype.title} (${archetype.serial})`;

    if (toneId === "quant") {
      return [
        `📐 Institutional Risk Decomposition for "${portfolioName}" (${archetype.serial}):`,
        "",
        `• Risk Score: ${data.score}/100 (${data.level} Risk)`,
        `• Archetype: ${archetype.title}`,
        `• Effective Assets (1/HHI): ${effectiveAssets}x | Top: ${topAsset} (${topWeight})`,
        `• Ann. Volatility: ${volatility} | Max Drawdown: ${maxDrawdown}`,
        "",
        `Audited with zero-hallucination deterministic math on @base #StocksMaxxing`,
      ].join("\n");
    }

    if (toneId === "challenge") {
      return [
        `⚡ My Base RWA & Crypto portfolio just earned the "${archetype.title}" badge on AUREN with a ${data.score}/100 Risk Score.`,
        "",
        `Top Conviction: ${topAsset} (${topWeight}) · 1/HHI Diversification: ${effectiveAssets}x · 2Y Return: ${Number(totalReturnPct) >= 0 ? "+" : ""}${totalReturnPct}%`,
        "",
        `Can your portfolio beat my risk-adjusted profile on @base? #StocksMaxxing`,
      ].join("\n");
    }

    return [
      `🛡️ "${portfolioName}" — ${archetype.title}`,
      `${tagLine}`,
      "",
      `📊 Risk Score: ${data.score}/100 (${data.level})`,
      `💎 Allocation: ${sortedWeights.map(([t, w]) => `${t} ${Math.round(w * 100)}%`).join(" · ")}`,
      `📉 Max Drawdown: ${maxDrawdown} | ⚡ Ann. Vol: ${volatility}`,
      "",
      `Deterministic B20 Tokenized Stock & DeFi risk engine on @base #StocksMaxxing`,
    ].join("\n");
  }, [
    toneId,
    customHandle,
    archetype,
    portfolioName,
    data.score,
    data.level,
    effectiveAssets,
    topAsset,
    topWeight,
    volatility,
    maxDrawdown,
    totalReturnPct,
    sortedWeights,
  ]);

  const getShareUrl = () => {
    const origin =
      typeof window !== "undefined" ? window.location.origin : "https://auren.app";
    const params = new URLSearchParams({
      score: String(data.score),
      level: data.level,
      portfolio: portfolioName,
      topAsset,
      topWeight,
      vol: volatility,
      mdd: maxDrawdown,
      eff: effectiveAssets,
      archetype: archetype.title,
      theme: themeId,
    });
    return `${origin}/dashboard?${params.toString()}`;
  };

  const handleShareToX = () => {
    const intentUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(
      shareText
    )}&url=${encodeURIComponent(getShareUrl())}`;
    window.open(intentUrl, "_blank", "noopener,noreferrer");
  };

  const handleCopyText = async () => {
    try {
      await navigator.clipboard.writeText(`${shareText}\n${getShareUrl()}`);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  const handleDownloadCard = () => {
    const canvas = document.createElement("canvas");
    canvas.width = 1200;
    canvas.height = 630;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // 1. Rich Gradient Background
    const bgGrad = ctx.createLinearGradient(0, 0, 1200, 630);
    bgGrad.addColorStop(0, theme.bgStart);
    bgGrad.addColorStop(1, theme.bgEnd);
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, 1200, 630);

    // Subtle radial glow behind gauge
    const radGrad = ctx.createRadialGradient(960, 220, 20, 960, 220, 340);
    radGrad.addColorStop(0, theme.accentSoft);
    radGrad.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = radGrad;
    ctx.fillRect(0, 0, 1200, 630);

    // Subtle institutional grid lines
    ctx.strokeStyle = "rgba(255, 255, 255, 0.03)";
    ctx.lineWidth = 1;
    for (let x = 60; x < 1200; x += 60) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, 630);
      ctx.stroke();
    }
    for (let y = 60; y < 630; y += 60) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(1200, y);
      ctx.stroke();
    }

    // Outer double luxury frame
    ctx.strokeStyle = theme.border;
    ctx.lineWidth = 2.5;
    ctx.strokeRect(24, 24, 1152, 582);
    ctx.strokeStyle = "rgba(255,255,255,0.08)";
    ctx.lineWidth = 1;
    ctx.strokeRect(32, 32, 1136, 566);

    // 2. Top Brand Header + Unique Serial Number
    ctx.fillStyle = theme.accent;
    ctx.fillRect(60, 56, 14, 14);
    ctx.fillStyle = "#F4F2ED";
    ctx.font = "bold 22px monospace";
    ctx.fillText("AUREN // BASE MAINNET RISK PASSPORT", 86, 71);

    // Serial & Tag Pill
    ctx.fillStyle = theme.panelBg;
    ctx.fillRect(820, 46, 320, 36);
    ctx.strokeStyle = theme.accent;
    ctx.lineWidth = 1.5;
    ctx.strokeRect(820, 46, 320, 36);
    ctx.fillStyle = theme.accent;
    ctx.font = "bold 13px monospace";
    ctx.fillText(`${theme.tag} · ${archetype.serial}`, 838, 69);

    // 3. Unique Investor Archetype Badge
    ctx.fillStyle = theme.accent;
    ctx.font = "bold 14px monospace";
    ctx.fillText(`INVESTOR ARCHETYPE // ${archetype.title}`, 60, 128);

    ctx.fillStyle = "#FFFFFF";
    ctx.font = "bold 40px sans-serif";
    ctx.fillText(portfolioName.slice(0, 30), 60, 174);

    ctx.fillStyle = "#9299A3";
    ctx.font = "17px sans-serif";
    ctx.fillText(
      customHandle.trim()
        ? `${archetype.subtitle} · Audited for ${customHandle.trim()}`
        : archetype.subtitle,
      60,
      204
    );

    // 4. Live Portfolio Equity Curve Sparkline Box (Left Center)
    ctx.fillStyle = theme.panelBg;
    ctx.fillRect(60, 228, 720, 150);
    ctx.strokeStyle = "rgba(255,255,255,0.1)";
    ctx.lineWidth = 1;
    ctx.strokeRect(60, 228, 720, 150);

    ctx.fillStyle = "#9299A3";
    ctx.font = "bold 12px monospace";
    ctx.fillText(
      `2Y INDEXED PERFORMANCE CURVE (${data.dates.length} SESSIONS)`,
      80,
      254
    );
    ctx.fillStyle = Number(totalReturnPct) >= 0 ? "#36A879" : "#EF4444";
    ctx.font = "bold 14px monospace";
    ctx.fillText(
      `${Number(totalReturnPct) >= 0 ? "+" : ""}${totalReturnPct}% CUMULATIVE`,
      570,
      254
    );

    // Draw actual portfolio price series curve
    const minP = Math.min(...portfolioSeries);
    const maxP = Math.max(...portfolioSeries);
    const plotX = 80,
      plotY = 270,
      plotW = 680,
      plotH = 92;

    ctx.beginPath();
    portfolioSeries.forEach((v, idx) => {
      const px = plotX + (idx / (portfolioSeries.length - 1)) * plotW;
      const py = plotY + plotH - ((v - minP) / (maxP - minP || 1)) * plotH;
      if (idx === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.strokeStyle = theme.accent;
    ctx.lineWidth = 3;
    ctx.stroke();

    // 5. Right Side: Circular Dial Risk Score Gauge
    const levelColor =
      data.level === "High"
        ? "#EF4444"
        : data.level === "Medium"
        ? "#F59E0B"
        : "#36A879";

    ctx.fillStyle = theme.panelBg;
    ctx.fillRect(810, 110, 330, 268);
    ctx.strokeStyle = levelColor;
    ctx.lineWidth = 2;
    ctx.strokeRect(810, 110, 330, 268);

    // Semi-circular gauge arc
    const cx = 975,
      cy = 248,
      radius = 88;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, Math.PI, 2 * Math.PI);
    ctx.strokeStyle = "#262936";
    ctx.lineWidth = 16;
    ctx.lineCap = "round";
    ctx.stroke();

    const endAngle = Math.PI + (Math.min(100, Math.max(0, data.score)) / 100) * Math.PI;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, Math.PI, endAngle);
    ctx.strokeStyle = levelColor;
    ctx.lineWidth = 16;
    ctx.lineCap = "round";
    ctx.stroke();

    ctx.fillStyle = "#FFFFFF";
    ctx.font = "bold 58px monospace";
    ctx.textAlign = "center";
    ctx.fillText(String(data.score), cx, cy - 10);

    ctx.fillStyle = levelColor;
    ctx.font = "bold 16px monospace";
    ctx.fillText(`${data.level.toUpperCase()} RISK / 100`, cx, cy + 24);

    ctx.fillStyle = "#9299A3";
    ctx.font = "12px monospace";
    ctx.fillText("DETERMINISTIC 6-RULE ENGINE", cx, cy + 54);
    ctx.textAlign = "left";

    // 6. Proportional Multi-Asset Allocation Bar
    let barX = 60;
    const barY = 400,
      barW = 1080,
      barH = 16;
    sortedWeights.forEach(([, weight], idx) => {
      const segW = Math.max(8, weight * barW);
      ctx.fillStyle = PALETTE_COLORS[idx % PALETTE_COLORS.length];
      ctx.fillRect(barX, barY, Math.min(segW, 1140 - barX), barH);
      barX += segW;
    });

    // Legend Pills under bar
    let pillX = 60;
    sortedWeights.forEach(([ticker, weight], idx) => {
      ctx.fillStyle = PALETTE_COLORS[idx % PALETTE_COLORS.length];
      ctx.fillRect(pillX, 428, 10, 10);
      ctx.fillStyle = "#F4F2ED";
      ctx.font = "bold 13px monospace";
      const label = `${ticker} ${Math.round(weight * 100)}%`;
      ctx.fillText(label, pillX + 16, 438);
      pillX += ctx.measureText(label).width + 44;
    });

    // 7. Bottom 4 Telemetry Metrics Strip
    const metrics = [
      { label: "TOP CONVICTION", value: `${topAsset} (${topWeight})`, color: "#FFFFFF" },
      { label: "EFFECTIVE ASSETS (1/HHI)", value: `${effectiveAssets}x`, color: theme.accent },
      { label: "ANNUALISED VOLATILITY", value: volatility, color: "#FFFFFF" },
      { label: "MAX HISTORICAL DRAWDOWN", value: maxDrawdown, color: "#EF4444" },
    ];

    metrics.forEach((m, idx) => {
      const mx = 60 + idx * 275;
      ctx.fillStyle = theme.panelBg;
      ctx.fillRect(mx, 460, 255, 86);
      ctx.strokeStyle = "rgba(255,255,255,0.08)";
      ctx.lineWidth = 1;
      ctx.strokeRect(mx, 460, 255, 86);

      ctx.fillStyle = "#9299A3";
      ctx.font = "bold 11px monospace";
      ctx.fillText(m.label, mx + 16, 486);

      ctx.fillStyle = m.color;
      ctx.font = "bold 26px monospace";
      ctx.fillText(m.value, mx + 16, 524);
    });

    // Footer
    ctx.fillStyle = "#9299A3";
    ctx.font = "13px monospace";
    ctx.fillText(
      "AUREN Risk Intelligence · Coinbase B20 Tokenized Stocks & Base DeFi · #StocksMaxxing",
      60,
      580
    );

    const link = document.createElement("a");
    link.download = `auren-passport-${themeId}-${data.score}.png`;
    link.href = canvas.toDataURL("image/png");
    link.click();
  };

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      title="Custom Risk Passport & X Scorecard Studio"
      description="Every portfolio generates a unique Investor Archetype, live equity curve sparkline, and serial hash. Choose a theme to download or share on X."
      size="lg"
    >
      <div className="space-y-5">
        {/* Theme & Handle Customizer Bar */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <label className="auren-eyebrow flex items-center gap-1.5">
              <Palette className="h-3.5 w-3.5 text-gold" />
              Select Card Edition Theme
            </label>
            <div className="mt-1.5 grid grid-cols-2 gap-1.5">
              {Object.values(CARD_THEMES).map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setThemeId(t.id)}
                  className={`flex items-center gap-2 rounded-lg border px-2.5 py-2 text-left font-mono text-[0.65rem] transition-all ${
                    themeId === t.id
                      ? "border-gold bg-gold/15 text-highlight font-bold"
                      : "border-line bg-obsidian text-muted hover:text-primary"
                  }`}
                >
                  <span
                    className="h-2.5 w-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: t.accent }}
                  />
                  <span className="truncate">{t.name}</span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label htmlFor="custom-x-handle" className="auren-eyebrow">
              Personalize Card (@Handle or ENS / Base Name)
            </label>
            <input
              id="custom-x-handle"
              type="text"
              value={customHandle}
              onChange={(e) => setCustomHandle(e.target.value)}
              placeholder="@yourhandle orvitalik.base.eth"
              className="mt-1.5 w-full rounded-lg border border-line bg-obsidian px-3 py-2 font-mono text-xs text-primary placeholder:text-faint focus:border-gold focus:outline-none"
            />
            <div className="mt-2 flex items-center gap-1.5">
              {(["maxxing", "quant", "challenge"] as TweetToneId[]).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setToneId(t)}
                  className={`rounded border px-2 py-1 font-mono text-[0.6rem] uppercase ${
                    toneId === t
                      ? "border-gold bg-gold/15 text-highlight"
                      : "border-line bg-obsidian text-muted"
                  }`}
                >
                  {t === "maxxing" ? "Base Flex" : t === "quant" ? "Quant Brief" : "Challenge"}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Live Interactive Card Preview */}
        <div
          className="relative overflow-hidden rounded-xl p-5 shadow-2xl transition-all"
          style={{
            background: `linear-gradient(135deg, ${theme.bgStart}, ${theme.bgEnd})`,
            border: `2px solid ${theme.border}`,
          }}
        >
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-3">
            <div className="flex items-center gap-2">
              <span
                className="h-3 w-3 rounded-xs"
                style={{ backgroundColor: theme.accent }}
              />
              <span className="font-mono text-xs font-bold tracking-[0.18em] text-primary">
                AUREN // RISK PASSPORT
              </span>
            </div>
            <span
              className="flex items-center gap-1.5 px-2.5 py-0.5 font-mono text-[0.6rem] font-bold uppercase tracking-[0.14em]"
              style={{
                border: `1px solid ${theme.accent}`,
                backgroundColor: theme.accentSoft,
                color: "#F4F2ED",
              }}
            >
              <ShieldCheck aria-hidden="true" className="h-3 w-3" />
              {theme.tag} · {archetype.serial}
            </span>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-[1.45fr_0.85fr] sm:items-center">
            <div>
              <div
                className="inline-flex items-center gap-1.5 font-mono text-[0.65rem] font-bold uppercase tracking-wider"
                style={{ color: theme.accent }}
              >
                <Sparkles className="h-3.5 w-3.5" />
                {archetype.title}
              </div>
              <h3 className="mt-1 text-xl font-bold text-primary">{portfolioName}</h3>
              <p className="mt-1 text-xs text-muted">
                {customHandle.trim()
                  ? `${archetype.subtitle} · Audited for ${customHandle.trim()}`
                  : archetype.subtitle}
              </p>

              {/* Stacked Proportional Bar */}
              <div className="mt-4 flex h-2.5 w-full overflow-hidden rounded-full bg-black/50">
                {sortedWeights.map(([tk, w], idx) => (
                  <div
                    key={tk}
                    style={{
                      width: `${Math.round(w * 100)}%`,
                      backgroundColor: PALETTE_COLORS[idx % PALETTE_COLORS.length],
                    }}
                    title={`${tk}: ${Math.round(w * 100)}%`}
                  />
                ))}
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                {sortedWeights.map(([tk, w], idx) => (
                  <span
                    key={tk}
                    className="flex items-center gap-1 font-mono text-[0.62rem] text-primary"
                  >
                    <span
                      className="h-2 w-2 rounded-full"
                      style={{
                        backgroundColor: PALETTE_COLORS[idx % PALETTE_COLORS.length],
                      }}
                    />
                    {tk} {Math.round(w * 100)}%
                  </span>
                ))}
              </div>
            </div>

            {/* Right Gauge Dial Preview */}
            <div
              className="flex flex-col items-center justify-center rounded-xl p-4 text-center"
              style={{
                backgroundColor: theme.panelBg,
                border: `1.5px solid ${theme.accent}`,
              }}
            >
              <span className="font-mono text-[0.6rem] uppercase tracking-widest text-muted">
                Deterministic Score
              </span>
              <span className="mt-1 font-mono text-4xl font-extrabold text-primary">
                {data.score}
                <span className="text-sm text-muted">/100</span>
              </span>
              <span
                className="mt-1 rounded px-2 py-0.5 font-mono text-[0.62rem] font-bold uppercase"
                style={{
                  backgroundColor: theme.accentSoft,
                  color: theme.accent,
                }}
              >
                {data.level} Risk · {Number(totalReturnPct) >= 0 ? "+" : ""}
                {totalReturnPct}% 2Y
              </span>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-2.5 border-t border-white/10 pt-3.5 sm:grid-cols-4">
            <div className="rounded-lg bg-black/30 p-2.5">
              <span className="block font-mono text-[0.58rem] uppercase text-muted">
                Top Conviction
              </span>
              <span className="mt-0.5 block font-mono text-xs font-bold text-primary">
                {topAsset} ({topWeight})
              </span>
            </div>
            <div className="rounded-lg bg-black/30 p-2.5">
              <span className="block font-mono text-[0.58rem] uppercase text-muted">
                Effective Assets
              </span>
              <span
                className="mt-0.5 block font-mono text-xs font-bold"
                style={{ color: theme.accent }}
              >
                {effectiveAssets}x (1/HHI)
              </span>
            </div>
            <div className="rounded-lg bg-black/30 p-2.5">
              <span className="block font-mono text-[0.58rem] uppercase text-muted">
                Ann. Volatility
              </span>
              <span className="mt-0.5 block font-mono text-xs font-bold text-primary">
                {volatility}
              </span>
            </div>
            <div className="rounded-lg bg-black/30 p-2.5">
              <span className="block font-mono text-[0.58rem] uppercase text-muted">
                Max Drawdown
              </span>
              <span className="mt-0.5 block font-mono text-xs font-bold text-negative">
                {maxDrawdown}
              </span>
            </div>
          </div>
        </div>

        {/* Pre-filled X Post Preview */}
        <div className="rounded-lg border border-line bg-secondary/60 p-3.5">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[0.62rem] uppercase tracking-[0.15em] text-muted">
              Personalized X Post ($50 USDC Bounty Eligible)
            </span>
            <button
              type="button"
              onClick={handleCopyText}
              className="flex items-center gap-1.5 font-mono text-[0.65rem] text-champagne hover:underline"
            >
              {copied ? (
                <>
                  <Check aria-hidden="true" className="h-3 w-3 text-positive" />
                  Copied
                </>
              ) : (
                <>
                  <Copy aria-hidden="true" className="h-3 w-3" />
                  Copy Text
                </>
              )}
            </button>
          </div>
          <pre className="mt-2 whitespace-pre-wrap font-mono text-xs leading-relaxed text-primary">
            {shareText}
          </pre>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
          <Button variant="secondary" onClick={handleDownloadCard} className="text-xs">
            <Download aria-hidden="true" className="h-3.5 w-3.5 text-gold" />
            Download Custom 1200×630 PNG
          </Button>
          <Button variant="primary" onClick={handleShareToX} className="text-xs">
            <Share2 aria-hidden="true" className="h-3.5 w-3.5" />
            Post Passport on X
            <ExternalLink aria-hidden="true" className="ml-1 h-3 w-3 opacity-80" />
          </Button>
        </div>
      </div>
    </Dialog>
  );
}

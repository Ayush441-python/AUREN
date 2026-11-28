import { ImageResponse } from "next/og";
import { NextRequest } from "next/server";

export const runtime = "edge";

const THEMES: Record<
  string,
  { bg: string; panel: string; accent: string; tag: string }
> = {
  "obsidian-gold": {
    bg: "#08090c",
    panel: "#11131a",
    accent: "#d6b56d",
    tag: "INSTITUTIONAL EDITION",
  },
  "base-cobalt": {
    bg: "#040814",
    panel: "#0a1328",
    accent: "#3b82f6",
    tag: "BASE MAINNET 8453",
  },
  "emerald-quant": {
    bg: "#050e0b",
    panel: "#0b1915",
    accent: "#36a879",
    tag: "ALPHA GUARDIAN",
  },
  "crimson-tactical": {
    bg: "#100608",
    panel: "#180b0e",
    accent: "#f43f5e",
    tag: "STRESS TESTED",
  },
};

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const score = searchParams.get("score") || "35";
  const level = searchParams.get("level") || "Medium";
  const portfolio = searchParams.get("portfolio") || "Base Tokenized Stocks & RWA";
  const topAsset = searchParams.get("topAsset") || "NVDA";
  const topWeight = searchParams.get("topWeight") || "30%";
  const volatility = searchParams.get("vol") || "24.2%";
  const drawdown = searchParams.get("mdd") || "-18.4%";
  const effAssets = searchParams.get("eff") || "4.8";
  const archetype = searchParams.get("archetype") || "SOVEREIGN RWA ARCHITECT";
  const themeKey = searchParams.get("theme") || "obsidian-gold";
  const theme = THEMES[themeKey] || THEMES["obsidian-gold"];

  const levelColor =
    level === "High" ? "#ef4444" : level === "Medium" ? "#f59e0b" : "#36a879";

  return new ImageResponse(
    (
      <div
        style={{
          height: "100%",
          width: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          backgroundColor: theme.bg,
          color: "#f3f4f6",
          padding: "52px 60px",
          fontFamily: "sans-serif",
          border: `3px solid ${theme.accent}`,
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
            <div
              style={{
                width: "16px",
                height: "16px",
                backgroundColor: theme.accent,
                display: "flex",
              }}
            />
            <span
              style={{
                fontSize: "26px",
                fontWeight: 700,
                letterSpacing: "0.2em",
                color: "#f5e6c8",
              }}
            >
              AUREN // RISK PASSPORT
            </span>
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              padding: "8px 18px",
              border: `1.5px solid ${theme.accent}`,
              backgroundColor: theme.panel,
              color: theme.accent,
              fontSize: "14px",
              fontWeight: 700,
              letterSpacing: "0.14em",
              textTransform: "uppercase",
            }}
          >
            {theme.tag} · B20 VERIFIED
          </div>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
            marginTop: "20px",
            marginBottom: "20px",
          }}
        >
          <div style={{ display: "flex", flexDirection: "column", maxWidth: "690px" }}>
            <span
              style={{
                fontSize: "15px",
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.18em",
                color: theme.accent,
                marginBottom: "10px",
              }}
            >
              INVESTOR ARCHETYPE // {archetype}
            </span>
            <span
              style={{
                fontSize: "46px",
                fontWeight: 700,
                color: "#ffffff",
                lineHeight: 1.15,
              }}
            >
              {portfolio}
            </span>
            <span
              style={{
                fontSize: "19px",
                color: "#9ca3af",
                marginTop: "14px",
              }}
            >
              Deterministic HHI concentration, drawdown &amp; volatility intelligence on Base.
            </span>
          </div>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              padding: "28px 44px",
              backgroundColor: theme.panel,
              border: `2.5px solid ${levelColor}`,
            }}
          >
            <span
              style={{
                fontSize: "13px",
                textTransform: "uppercase",
                letterSpacing: "0.18em",
                color: "#9ca3af",
              }}
            >
              Risk Score
            </span>
            <span
              style={{
                fontSize: "76px",
                fontWeight: 800,
                color: levelColor,
                lineHeight: 1.05,
                marginTop: "6px",
              }}
            >
              {score}
            </span>
            <span
              style={{
                fontSize: "17px",
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.14em",
                color: levelColor,
                marginTop: "6px",
              }}
            >
              {level} Risk / 100
            </span>
          </div>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            width: "100%",
            gap: "18px",
            borderTop: "1px solid #262936",
            paddingTop: "26px",
          }}
        >
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span style={{ fontSize: "13px", color: "#9ca3af", textTransform: "uppercase" }}>
              Top Conviction
            </span>
            <span style={{ fontSize: "26px", fontWeight: 700, color: "#ffffff", marginTop: "4px" }}>
              {topAsset} ({topWeight})
            </span>
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span style={{ fontSize: "13px", color: "#9ca3af", textTransform: "uppercase" }}>
              Effective Assets (1/HHI)
            </span>
            <span
              style={{
                fontSize: "26px",
                fontWeight: 700,
                color: theme.accent,
                marginTop: "4px",
              }}
            >
              {effAssets}x
            </span>
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span style={{ fontSize: "13px", color: "#9ca3af", textTransform: "uppercase" }}>
              Annualised Volatility
            </span>
            <span style={{ fontSize: "26px", fontWeight: 700, color: "#ffffff", marginTop: "4px" }}>
              {volatility}
            </span>
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span style={{ fontSize: "13px", color: "#9ca3af", textTransform: "uppercase" }}>
              Max Historical Drawdown
            </span>
            <span style={{ fontSize: "26px", fontWeight: 700, color: "#ef4444", marginTop: "4px" }}>
              {drawdown}
            </span>
          </div>
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
    }
  );
}

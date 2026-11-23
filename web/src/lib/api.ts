import {
  RiskAnalysis,
  LiquidityAnalysis,
  WalletResponse,
  AIReportResponse,
  UniverseData,
} from "./types";

export const PUBLIC_API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL || "https://auren-api-8yrq.onrender.com"
).replace(/\/+$/, "");

const getApiBase = (): string => {
  if (typeof window !== "undefined") {
    const saved = localStorage.getItem("auren_api_url");
    if (saved) return saved.replace(/\/+$/, "");
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
      return "http://127.0.0.1:8000";
    }
  }
  return PUBLIC_API_BASE_URL;
};

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const base = getApiBase();
  const url = `${base}${endpoint}`;

  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!res.ok) {
    let errorMsg = `Server error (${res.status})`;
    try {
      const data = await res.json();
      if (data && data.detail) {
        errorMsg = Array.isArray(data.detail)
          ? data.detail.map((x: any) => x.msg || JSON.stringify(x)).join("; ")
          : String(data.detail);
      }
    } catch {
      // Non-JSON response
    }
    throw new Error(errorMsg);
  }

  return res.json();
}

export async function fetchUniverse(): Promise<UniverseData> {
  return request<UniverseData>("/universe");
}

export async function calculateRisk(
  weights: Record<string, number>,
  period: string = "2y"
): Promise<RiskAnalysis> {
  return request<RiskAnalysis>("/risk", {
    method: "POST",
    body: JSON.stringify({ weights, period }),
  });
}

export async function calculateLiquidity(
  portfolioValue: number,
  weights: Record<string, number>,
  advParticipation: number = 0.1,
  period: string = "1y"
): Promise<LiquidityAnalysis> {
  return request<LiquidityAnalysis>("/liquidity", {
    method: "POST",
    body: JSON.stringify({
      portfolio_value: portfolioValue,
      weights,
      adv_participation: advParticipation,
      period,
    }),
  });
}

export async function inspectWallet(
  address: string,
  rpcUrl?: string
): Promise<WalletResponse> {
  return request<WalletResponse>("/wallet", {
    method: "POST",
    body: JSON.stringify({ address, rpc_url: rpcUrl || null }),
  });
}

export async function generateAIReport(
  metrics: Record<string, any>,
  model?: string
): Promise<AIReportResponse> {
  return request<AIReportResponse>("/report", {
    method: "POST",
    body: JSON.stringify({ metrics, model: model || null }),
  });
}

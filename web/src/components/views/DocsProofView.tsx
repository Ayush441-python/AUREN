"use client";

import React, { useState } from "react";
import { ShieldCheck, Code, BookOpen, Terminal, Check, Copy } from "lucide-react";

export function DocsProofView() {
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const curlExample = `curl -X POST https://api.auren.fi/risk \\
  -H "Content-Type: application/json" \\
  -d '{
    "weights": {
      "AAPL": 0.35,
      "NVDA": 0.25,
      "ETH-USD": 0.20,
      "BTC-USD": 0.15,
      "USDC": 0.05
    },
    "period": "2y"
  }'`;

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="border-b border-[#26262C] pb-5">
        <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-[#F5F6F7]">
          Methodology, Proofs & API Reference
        </h1>
        <p className="mt-1 text-xs sm:text-sm text-[#A1A4AB]">
          Complete mathematical formulations, statistical definitions, and programmatic API endpoints.
        </p>
      </div>

      {/* Mathematical Proofs Section */}
      <div className="space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[#6B6E76] flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-[#E3B341]" />
          <span>Core Quantitative Formulations</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Formula 1 */}
          <div className="panel-card p-5">
            <h3 className="text-sm font-semibold text-[#F5F6F7]">1. Portfolio Volatility (&sigma;)</h3>
            <p className="text-xs text-[#A1A4AB] mt-1">
              Annualized standard deviation derived from the asset return covariance matrix.
            </p>
            <div className="mt-3 rounded-md bg-[#0E0E10] p-3 font-mono text-xs text-[#E3B341] border border-[#26262C]">
              &sigma;_p = &radic;(w^T &times; &Sigma; &times; w) &times; &radic;252
            </div>
            <p className="mt-2 text-[11px] text-[#6B6E76]">
              Where w is the normalized weight vector and &Sigma; is the 252-day daily covariance matrix.
            </p>
          </div>

          {/* Formula 2 */}
          <div className="panel-card p-5">
            <h3 className="text-sm font-semibold text-[#F5F6F7]">2. Effective Assets (N_eff)</h3>
            <p className="text-xs text-[#A1A4AB] mt-1">
              Inverse Herfindahl-Hirschman Index accounting for capital weighting skew.
            </p>
            <div className="mt-3 rounded-md bg-[#0E0E10] p-3 font-mono text-xs text-[#7FB3A6] border border-[#26262C]">
              HHI = &Sigma; (w_i)^2 &nbsp;&nbsp;|&nbsp;&nbsp; N_eff = 1 / HHI
            </div>
            <p className="mt-2 text-[11px] text-[#6B6E76]">
              A 5-asset portfolio heavily weighted in one stock will reflect an N_eff closer to 1.5 than 5.
            </p>
          </div>

          {/* Formula 3 */}
          <div className="panel-card p-5">
            <h3 className="text-sm font-semibold text-[#F5F6F7]">3. Maximum Drawdown (MDD)</h3>
            <p className="text-xs text-[#A1A4AB] mt-1">
              The maximum observed loss from a historical peak to a subsequent trough.
            </p>
            <div className="mt-3 rounded-md bg-[#0E0E10] p-3 font-mono text-xs text-[#E07A5F] border border-[#26262C]">
              {"MDD = min_t ( (V_t - max_t V_t) / max_t V_t )"}
            </div>
            <p className="mt-2 text-[11px] text-[#6B6E76]">
              Evaluates worst-case historical capital impairment before full recovery.
            </p>
          </div>

          {/* Formula 4 */}
          <div className="panel-card p-5">
            <h3 className="text-sm font-semibold text-[#F5F6F7]">4. Multi-Asset Alignment (Forward-Fill)</h3>
            <p className="text-xs text-[#A1A4AB] mt-1">
              Resolves non-overlapping trading days between equities (252d) and crypto (365d).
            </p>
            <div className="mt-3 rounded-md bg-[#0E0E10] p-3 font-mono text-xs text-[#F5F6F7] border border-[#26262C]">
              P_aligned[t] = P[t].ffill(limit=3)
            </div>
            <p className="mt-2 text-[11px] text-[#6B6E76]">
              Preserves price continuity over weekend non-trading sessions without discarding crypto data.
            </p>
          </div>
        </div>
      </div>

      {/* Programmatic API Reference */}
      <div className="space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[#6B6E76] flex items-center gap-2">
          <Terminal className="h-4 w-4 text-[#E3B341]" />
          <span>Risk Engine HTTP Endpoints</span>
        </h2>

        <div className="panel-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 font-mono text-xs">
              <span className="rounded bg-[#E3B341]/10 px-2 py-0.5 font-bold text-[#E3B341] border border-[#E3B341]/20">
                POST
              </span>
              <span className="text-[#F5F6F7]">/risk</span>
            </div>
            <button
              onClick={() => copyToClipboard(curlExample, "curl")}
              className="flex items-center gap-1.5 rounded bg-[#1C1C21] px-2.5 py-1 text-xs text-[#A1A4AB] hover:text-[#F5F6F7] border border-[#26262C]"
            >
              {copiedCode === "curl" ? <Check className="h-3 w-3 text-[#7FB3A6]" /> : <Copy className="h-3 w-3" />}
              <span>{copiedCode === "curl" ? "Copied" : "Copy cURL"}</span>
            </button>
          </div>

          <pre className="overflow-x-auto rounded-lg border border-[#26262C] bg-[#0E0E10] p-4 font-mono text-xs text-[#A1A4AB] leading-relaxed">
            {curlExample}
          </pre>

          <div className="text-xs text-[#6B6E76]">
            Returns aggregate risk score, level, component penalties, covariance correlation matrix, sector exposures, and historical scenario stress results.
          </div>
        </div>
      </div>
    </div>
  );
}

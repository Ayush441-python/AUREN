"use client";

import { BookOpen, Braces, ShieldCheck, Terminal } from "lucide-react";
import { PUBLIC_API_BASE_URL } from "@/lib/api";
import { formatNumber, formatPercent, formatSignedPercent } from "@/lib/format";
import type { RiskAnalysis } from "@/lib/types";
import { Panel, PanelHeader } from "@/components/ui/Panel";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { RiskBadge } from "@/components/ui/RiskBadge";

interface DocsProofViewProps {
  data?: RiskAnalysis;
}

const riskEndpoint = PUBLIC_API_BASE_URL + "/risk";

const rules = [
  {
    rule: "Largest single asset above 30%",
    points: "+20",
    source: "max(normalized_weights) > 0.30",
  },
  {
    rule: "Effective assets below 4",
    points: "+15",
    source: "1 / HHI < 4",
  },
  {
    rule: "Annualized volatility above 30%",
    points: "+20",
    source: "std(daily simple returns) × √252 > 0.30",
  },
  {
    rule: "Maximum drawdown below −30%",
    points: "+15",
    source: "min(P_t / running peak − 1) < −0.30",
  },
  {
    rule: "Two or more pairs with r above 0.70",
    points: "+15",
    source: "Pearson r on aligned daily simple returns",
  },
  {
    rule: "Largest sector group above 50%",
    points: "+15",
    source: "grouped normalized weight > 0.50",
  },
];

const curlExample = `curl -X POST ${riskEndpoint} \\
  -H "Content-Type: application/json" \\
  -d '{
    "weights": {
      "NVDA": 0.40,
      "MSFT": 0.30,
      "GOOGL": 0.20,
      "ETH-USD": 0.10
    },
    "period": "2y"
  }'`;

const fetchExample = `const response = await fetch(
  "${riskEndpoint}",
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      weights: { NVDA: 0.40, MSFT: 0.30, GOOGL: 0.20, "ETH-USD": 0.10 },
      period: "2y",
    }),
  }
);

const analysis = await response.json();`;

const responseShapeExample = `{
  "score": 0,
  "level": "Low | Medium | High",
  "normalized_weights": { "NVDA": 0.4 },
  "reasons": [],
  "hits": [],
  "dates": ["YYYY-MM-DD"],
  "price_series": { "Portfolio": [100] },
  "drawdown_series": [0],
  "correlation_matrix": { "columns": ["NVDA"], "data": [[1]] },
  "concentration": {
    "top_asset": "NVDA",
    "top_weight": 0.4,
    "top3_weight": 0.9,
    "hhi": 0.3,
    "effective_assets": 3.33
  },
  "volatility": 0.2,
  "max_drawdown": -0.1,
  "sector_exposure": { "Big Tech": 0.9 },
  "correlated_pairs": [],
  "stress": { "Scenario name": -0.1 },
  "worst_historical_periods": { "worst_day": -0.05, "worst_month": -0.12 },
  "disclaimer": "Analytics only, not investment advice."
}`;

const endpoints = [
  {
    method: "POST",
    path: "/risk",
    body: "{ weights, period }",
    purpose: "Calculate the full deterministic risk analysis.",
  },
  {
    method: "POST",
    path: "/liquidity",
    body: "{ portfolio_value, weights, adv_participation, period }",
    purpose: "Estimate average daily value participation and exit duration.",
  },
  {
    method: "POST",
    path: "/wallet",
    body: "{ address, rpc_url }",
    purpose: "Inspect a public EVM address for supported holdings.",
  },
  {
    method: "POST",
    path: "/report",
    body: "{ metrics, model }",
    purpose: "Generate an AI narrative from a supplied metrics object.",
  },
  {
    method: "GET",
    path: "/universe",
    body: "—",
    purpose: "List supported tickers, sectors, and groups.",
  },
  {
    method: "GET",
    path: "/rules",
    body: "—",
    purpose: "Return the deterministic scoring rule table.",
  },
];

export function DocsProofView({ data }: DocsProofViewProps) {
  return (
    <div className="space-y-7">
      <header className="border-b border-line pb-6">
        <p className="auren-eyebrow">Portfolio intelligence / Methodology</p>
        <h1 className="mt-3 font-display text-4xl leading-none text-primary sm:text-5xl">
          Proofs & API
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted">
          Exact formulas, scoring thresholds, and programmatic access. The examples below use the
          same API base resolution as the dashboard: the local backend on localhost, an explicit
          <code className="mx-1 font-mono text-champagne">auren_api_url</code> browser override, or
          the configured deployment base.
        </p>
      </header>

      {data && (
        <Panel>
          <PanelHeader
            eyebrow="Current analysis"
            title="Live snapshot"
            action={<RiskBadge level={data.level} score={data.score} />}
          />
          <div className="grid grid-cols-1 gap-px bg-line sm:grid-cols-2 xl:grid-cols-4">
            <div className="bg-secondary px-5 py-4">
              <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">Volatility</p>
              <p className="mt-2 font-mono text-lg text-primary tabular">{formatPercent(data.volatility)}</p>
            </div>
            <div className="bg-secondary px-5 py-4">
              <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">Max drawdown</p>
              <p className="mt-2 font-mono text-lg text-negative tabular">
                {formatSignedPercent(data.max_drawdown)}
              </p>
            </div>
            <div className="bg-secondary px-5 py-4">
              <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">HHI</p>
              <p className="mt-2 font-mono text-lg text-primary tabular">
                {formatNumber(data.concentration.hhi, 4)}
              </p>
            </div>
            <div className="bg-secondary px-5 py-4">
              <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">Worst 21 sessions</p>
              <p className="mt-2 font-mono text-lg text-negative tabular">
                {formatSignedPercent(data.worst_historical_periods.worst_month)}
              </p>
            </div>
          </div>
        </Panel>
      )}

      <Panel>
        <PanelHeader
          eyebrow="Scoring"
          title="Deterministic rule table"
          action={<ShieldCheck aria-hidden="true" className="h-4 w-4 text-gold" />}
        />
        <div className="auren-scrollbar-none overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-xs">
            <caption className="sr-only">Deterministic risk scoring rules</caption>
            <thead className="border-b border-line bg-secondary/60 text-faint">
              <tr>
                <th scope="col" className="px-5 py-3 font-mono text-[0.6rem] uppercase tracking-[0.16em]">
                  Condition
                </th>
                <th scope="col" className="px-5 py-3 font-mono text-[0.6rem] uppercase tracking-[0.16em]">
                  Penalty
                </th>
                <th scope="col" className="px-5 py-3 font-mono text-[0.6rem] uppercase tracking-[0.16em]">
                  Computation
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line/60">
              {rules.map((item) => (
                <tr key={item.rule} className="text-muted">
                  <th scope="row" className="px-5 py-3 font-normal text-primary">
                    {item.rule}
                  </th>
                  <td className="px-5 py-3 font-mono text-champagne tabular">{item.points}</td>
                  <td className="px-5 py-3 font-mono text-[0.68rem]">{item.source}</td>
                </tr>
              ))}
            </tbody>
            <tfoot className="border-t border-line bg-secondary/40">
              <tr>
                <th scope="row" className="px-5 py-3 font-normal text-primary">
                  Final tier
                </th>
                <td className="px-5 py-3 font-mono text-champagne">0–100</td>
                <td className="px-5 py-3 font-mono text-[0.68rem] text-muted">
                  0–34 Low · 35–64 Medium · 65–100 High
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </Panel>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Panel>
          <PanelHeader
            eyebrow="Formulation 01"
            title="Concentration & volatility"
            action={<BookOpen aria-hidden="true" className="h-4 w-4 text-gold" />}
          />
          <div className="space-y-5 p-5 sm:p-6">
            <Formula
              label="Herfindahl–Hirschman Index"
              code="HHI = Σ (wᵢ)²"
              detail="Weights are normalized before calculation. A single-asset portfolio has HHI = 1."
            />
            <Formula
              label="Effective number of assets"
              code="N_eff = 1 / HHI"
              detail="Below 4 adds 15 penalty points."
            />
            <Formula
              label="Annualized volatility"
              code="σ_p = stdev(simple daily returns) × √252"
              detail="Above 30% adds 20 penalty points."
            />
          </div>
        </Panel>

        <Panel>
          <PanelHeader
            eyebrow="Formulation 02"
            title="Drawdown & co-movement"
            action={<Braces aria-hidden="true" className="h-4 w-4 text-gold" />}
          />
          <div className="space-y-5 p-5 sm:p-6">
            <Formula
              label="Maximum drawdown"
              code="MDD = min(Pₜ / running_max(P) − 1)"
              detail="Below −30% adds 15 penalty points."
            />
            <Formula
              label="Pearson correlation"
              code="r = cov(rᵢ, rⱼ) / (σᵢσⱼ)"
              detail="Uses aligned daily simple returns. Two or more pairs above 0.70 add 15 points."
            />
            <Formula
              label="Worst month"
              code="min rolling 21-session portfolio return"
              detail="This is a trading-session window, not a 30-calendar-day window."
            />
            <Formula
              label="Stress scenarios"
              code="shock response = Σ (wᵢ × scenarioᵢ)"
              detail="Hypothetical shocks under current weights; not historical replays."
            />
          </div>
        </Panel>
      </div>

      <Panel>
        <PanelHeader
          eyebrow="HTTP reference"
          title="Risk engine endpoints"
          action={<Terminal aria-hidden="true" className="h-4 w-4 text-gold" />}
        />
        <div className="p-5 sm:p-6">
          <div className="auren-scrollbar-none mb-6 overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-xs">
              <caption className="sr-only">Available API endpoints</caption>
              <thead className="border-b border-line text-faint">
                <tr>
                  <th scope="col" className="px-3 py-3 font-mono text-[0.6rem] uppercase tracking-[0.16em]">Method</th>
                  <th scope="col" className="px-3 py-3 font-mono text-[0.6rem] uppercase tracking-[0.16em]">Path</th>
                  <th scope="col" className="px-3 py-3 font-mono text-[0.6rem] uppercase tracking-[0.16em]">Body</th>
                  <th scope="col" className="px-3 py-3 font-mono text-[0.6rem] uppercase tracking-[0.16em]">Purpose</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/60">
                {endpoints.map((endpoint) => (
                  <tr key={`${endpoint.method}-${endpoint.path}`} className="text-muted">
                    <td className="px-3 py-3 font-mono text-champagne">{endpoint.method}</td>
                    <td className="px-3 py-3 font-mono text-primary">{endpoint.path}</td>
                    <td className="px-3 py-3 font-mono text-[0.68rem]">{endpoint.body}</td>
                    <td className="px-3 py-3">{endpoint.purpose}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
            <div className="space-y-3">
              <p className="auren-eyebrow">cURL</p>
              <CodeBlock code={curlExample} title="POST /risk" />
            </div>
            <div className="space-y-3">
              <p className="auren-eyebrow">TypeScript</p>
              <CodeBlock code={fetchExample} title="client.ts" />
            </div>
          </div>

          <div className="mt-6 space-y-3">
            <p className="auren-eyebrow">Response shape</p>
            <CodeBlock code={responseShapeExample} title="RiskAnalysis" />
          </div>

          <p className="mt-5 text-xs leading-relaxed text-faint">
            The browser client resolves its base from the <code className="font-mono text-champagne">auren_api_url</code> local storage override, localhost, or NEXT_PUBLIC_API_URL. No other API host is assumed.
          </p>
        </div>
      </Panel>
    </div>
  );
}

function Formula({
  label,
  code,
  detail,
}: {
  label: string;
  code: string;
  detail: string;
}) {
  return (
    <div className="border-l border-line pl-4">
      <p className="font-mono text-[0.6rem] uppercase tracking-[0.16em] text-champagne">{label}</p>
      <p className="mt-2 overflow-x-auto font-mono text-sm text-primary">{code}</p>
      <p className="mt-2 text-xs leading-relaxed text-muted">{detail}</p>
    </div>
  );
}

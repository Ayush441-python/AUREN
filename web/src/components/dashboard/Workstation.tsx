"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { BASE_PORTFOLIO_ANALYSIS } from "@/lib/mock";
import { calculateRisk } from "@/lib/api";
import { useWallet } from "@/lib/useWallet";
import type { RiskAnalysis } from "@/lib/types";
import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { OverviewView } from "@/components/views/OverviewView";
import { ExposureView } from "@/components/views/ExposureView";
import { CorrelationView } from "@/components/views/CorrelationView";
import { StressView } from "@/components/views/StressView";
import { ReportView } from "@/components/views/ReportView";
import { DocsProofView } from "@/components/views/DocsProofView";
import { PortfolioBuilderModal } from "@/components/modals/PortfolioBuilderModal";
import { WalletConnectModal } from "@/components/modals/WalletConnectModal";

export type DashboardTab =
  | "overview"
  | "exposure"
  | "correlation"
  | "stress"
  | "report"
  | "docs";

export type DataStatus = "reference" | "live" | "stale";

export interface SimulationComparison {
  baseline: RiskAnalysis;
  result: RiskAnalysis;
  weights: Record<string, number>;
}

export interface WorkstationProps {
  initialTab: DashboardTab;
  openBuilder?: boolean;
  portfolioId?: string;
}

const isDashboardTab = (value: string): value is DashboardTab =>
  value === "overview" ||
  value === "exposure" ||
  value === "correlation" ||
  value === "stress" ||
  value === "report" ||
  value === "docs";

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback;
}

export function Workstation({
  initialTab,
  openBuilder = false,
  portfolioId,
}: WorkstationProps) {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<DashboardTab>(initialTab);
  const [data, setData] = useState<RiskAnalysis>(BASE_PORTFOLIO_ANALYSIS);
  const [dataStatus, setDataStatus] = useState<DataStatus>("reference");
  const [customPortfolioName, setCustomPortfolioName] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [builderOpen, setBuilderOpen] = useState(openBuilder);
  const [walletOpen, setWalletOpen] = useState(false);
  const [simulation, setSimulation] = useState<SimulationComparison | null>(null);
  const customPortfolioApplied = useRef(false);

  const wallet = useWallet();
  const portfolioName =
    customPortfolioName ??
    (portfolioId ? `Portfolio ${portfolioId}` : "Balanced Multi-Asset");

  const buildHref = useCallback(
    (tab: DashboardTab) => {
      const params = new URLSearchParams();
      params.set("tab", tab);
      if (portfolioId) params.set("portfolio", portfolioId);
      return `/dashboard?${params.toString()}`;
    },
    [portfolioId]
  );

  const selectTab = useCallback(
    (tab: DashboardTab) => {
      if (!isDashboardTab(tab)) return;
      setActiveTab(tab);
      router.push(buildHref(tab), { scroll: false });
    },
    [buildHref, router]
  );

  useEffect(() => {
    const frame = requestAnimationFrame(() => setActiveTab(initialTab));
    return () => cancelAnimationFrame(frame);
  }, [initialTab]);

  useEffect(() => {
    let active = true;
    calculateRisk(BASE_PORTFOLIO_ANALYSIS.normalized_weights)
      .then((live) => {
        if (!active || !live || typeof live.score !== "number" || customPortfolioApplied.current) return;
        setData(live);
        setDataStatus("live");
        setError(null);
      })
      .catch((loadError: unknown) => {
        if (!active || customPortfolioApplied.current) return;
        setDataStatus("reference");
        setError(
          `Live analysis unavailable: ${errorMessage(
            loadError,
            "the risk engine did not respond"
          )}. Showing the bundled reference analysis.`
        );
      })
      .finally(() => {
        if (active && !customPortfolioApplied.current) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const handleApplyPortfolio = useCallback(
    async (weights: Record<string, number>, name: string) => {
      const previousStatus = dataStatus;
      customPortfolioApplied.current = true;
      setCustomPortfolioName(name);
      setLoading(true);
      setError(null);
      setSimulation(null);
      try {
        const live = await calculateRisk(weights);
        if (!live || typeof live.score !== "number") {
          throw new Error("The risk engine returned an incomplete analysis.");
        }
        setData(live);
        setDataStatus("live");
        selectTab("overview");
      } catch (applyError) {
        setDataStatus("stale");
        setError(
          `Could not analyze "${name}": ${errorMessage(
            applyError,
            "the risk engine did not respond"
          )}. The new weights were not applied. Showing the previous ${
            previousStatus === "live" ? "live" : "reference"
          } analysis.`
        );
      } finally {
        setLoading(false);
      }
    },
    [dataStatus, selectTab]
  );

  const handleSimulate = useCallback(
    async (newWeights: Record<string, number>) => {
      customPortfolioApplied.current = true;
      setLoading(true);
      setError(null);
      try {
        const live = await calculateRisk(newWeights);
        if (!live || typeof live.score !== "number") {
          throw new Error("The risk engine returned an incomplete analysis.");
        }
        setSimulation({ baseline: data, result: live, weights: newWeights });
        setData(live);
        setDataStatus("live");
      } catch (simulateError) {
        setDataStatus("stale");
        setError(
          `Recalculation failed: ${errorMessage(
            simulateError,
            "the risk engine did not respond"
          )}. Sandbox weights were not applied; the previous analysis is still displayed.`
        );
      } finally {
        setLoading(false);
      }
    },
    [data]
  );

  const closeBuilder = useCallback(() => {
    setBuilderOpen(false);
    if (openBuilder) {
      router.replace(buildHref(activeTab), { scroll: false });
    }
  }, [activeTab, buildHref, openBuilder, router]);

  return (
    <>
      <DashboardShell
        activeTab={activeTab}
        onSelectTab={selectTab}
        portfolioName={portfolioName}
        portfolioId={portfolioId}
        dataStatus={dataStatus}
        loading={loading}
        error={error}
        walletAddress={wallet.address}
        onNewPortfolio={() => setBuilderOpen(true)}
        onOpenWallet={() => setWalletOpen(true)}
        onOpenBuilder={() => setBuilderOpen(true)}
        onApplyPreset={handleApplyPortfolio}
        onDismissError={() => setError(null)}
      >
        {activeTab === "overview" && (
          <OverviewView
            data={data}
            status={dataStatus}
            error={error}
            portfolioName={portfolioName}
            onNavigateTab={selectTab}
          />
        )}
        {activeTab === "exposure" && <ExposureView data={data} />}
        {activeTab === "correlation" && <CorrelationView data={data} />}
        {activeTab === "stress" && (
          <StressView
            data={data}
            onSimulate={handleSimulate}
            isSimulating={loading}
            simulation={simulation}
            error={error}
          />
        )}
        {activeTab === "report" && <ReportView data={data} />}
        {activeTab === "docs" && <DocsProofView data={data} />}
      </DashboardShell>

      <PortfolioBuilderModal
        isOpen={builderOpen}
        onClose={closeBuilder}
        onApplyPortfolio={handleApplyPortfolio}
      />
      <WalletConnectModal
        isOpen={walletOpen}
        onClose={() => setWalletOpen(false)}
        isConnected={wallet.isConnected}
        connectedAddress={wallet.address}
        onConnectBrowser={wallet.connect}
        onDisconnect={wallet.disconnect}
        onSelectPortfolio={handleApplyPortfolio}
        hasProvider={wallet.hasProvider}
      />
    </>
  );
}

export default Workstation;

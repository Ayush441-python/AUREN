"use client";

import React, { useCallback, useState } from "react";
import { AppShell, NavTab } from "@/components/shell/AppShell";
import { BASE_PORTFOLIO_ANALYSIS } from "@/lib/mock";
import { calculateRisk } from "@/lib/api";
import type { RiskAnalysis } from "@/lib/types";
import type { SimulationComparison } from "@/components/dashboard/Workstation";
import { OverviewView } from "@/components/views/OverviewView";
import { ExposureView } from "@/components/views/ExposureView";
import { CorrelationView } from "@/components/views/CorrelationView";
import { StressView } from "@/components/views/StressView";
import { ReportView } from "@/components/views/ReportView";
import { SlidesView } from "@/components/views/SlidesView";
import { DocsProofView } from "@/components/views/DocsProofView";
import { PortfolioBuilderModal } from "@/components/modals/PortfolioBuilderModal";
import { useParams } from "next/navigation";

export default function PortfolioDetailPage() {
  const params = useParams();
  const id = params?.id as string;
  const [activeTab, setActiveTab] = useState<NavTab>("overview");
  const [builderModalOpen, setBuilderModalOpen] = useState(false);
  const [data, setData] = useState<RiskAnalysis>(BASE_PORTFOLIO_ANALYSIS);
  const [portfolioName, setPortfolioName] = useState<string>(`Portfolio: ${id || "Analysis"}`);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [simulation, setSimulation] = useState<SimulationComparison | null>(null);

  const handleApplyPortfolio = useCallback(async (weights: Record<string, number>, name: string) => {
    setPortfolioName(name);
    setLoading(true);
    setError(null);
    setSimulation(null);
    try {
      const live = await calculateRisk(weights);
      setData(live);
      setActiveTab("overview");
    } catch (err) {
      setError(err instanceof Error && err.message ? err.message : "Failed to analyze portfolio.");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSimulate = useCallback(
    async (newWeights: Record<string, number>) => {
      setLoading(true);
      setError(null);
      try {
        const live = await calculateRisk(newWeights);
        setSimulation({ baseline: data, result: live, weights: newWeights });
        setData(live);
      } catch (err) {
        setError(err instanceof Error && err.message ? err.message : "Failed to recalculate stress weights.");
      } finally {
        setLoading(false);
      }
    },
    [data]
  );

  return (
    <AppShell
      activeTab={activeTab}
      onSelectTab={setActiveTab}
      portfolioName={portfolioName}
      onNewPortfolio={() => setBuilderModalOpen(true)}
      onOpenWalletModal={() => setBuilderModalOpen(true)}
      onSelectPortfolio={handleApplyPortfolio}
    >
      {error && (
        <div
          role="alert"
          className="mb-4 rounded-md border border-[#E05252]/40 bg-[#E05252]/10 px-4 py-2.5 text-xs text-[#F5F6F7]"
        >
          {error}
        </div>
      )}
      {activeTab === "overview" && (
        <OverviewView data={data} onNavigateTab={setActiveTab} error={error} portfolioName={portfolioName} />
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
      {activeTab === "slides" && <SlidesView data={data} />}
      {activeTab === "docs" && <DocsProofView data={data} />}

      <PortfolioBuilderModal
        isOpen={builderModalOpen}
        onClose={() => setBuilderModalOpen(false)}
        onApplyPortfolio={handleApplyPortfolio}
      />
    </AppShell>
  );
}

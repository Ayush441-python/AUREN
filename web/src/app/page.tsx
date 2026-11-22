"use client";

import React, { useState, useEffect } from "react";
import { AppShell } from "@/components/shell/AppShell";
import { NavTab } from "@/components/shell/Sidebar";
import { BASE_PORTFOLIO_ANALYSIS } from "@/lib/mock";
import { RiskAnalysis } from "@/lib/types";
import { calculateRisk, inspectWallet } from "@/lib/api";
import { useWallet } from "@/lib/useWallet";
import { OverviewView } from "@/components/views/OverviewView";
import { ExposureView } from "@/components/views/ExposureView";
import { CorrelationView } from "@/components/views/CorrelationView";
import { StressView } from "@/components/views/StressView";
import { ReportView } from "@/components/views/ReportView";
import { DocsProofView } from "@/components/views/DocsProofView";
import { PortfolioBuilderModal } from "@/components/modals/PortfolioBuilderModal";
import { WalletConnectModal } from "@/components/modals/WalletConnectModal";

export default function WorkstationPage() {
  const [activeTab, setActiveTab] = useState<NavTab>("overview");
  const [portfolioName, setPortfolioName] = useState("Balanced Multi-Asset");
  const [data, setData] = useState<RiskAnalysis>(BASE_PORTFOLIO_ANALYSIS);
  const [builderModalOpen, setBuilderModalOpen] = useState(false);
  const [walletModalOpen, setWalletModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Real Web3 EVM Hook
  const {
    address: connectedAddress,
    isConnected,
    connect: connectBrowserWallet,
    disconnect: disconnectWallet,
    hasProvider,
  } = useWallet();

  // Load initial calculation from live backend if reachable
  useEffect(() => {
    async function loadInitial() {
      try {
        const live = await calculateRisk(BASE_PORTFOLIO_ANALYSIS.normalized_weights);
        if (live && live.score !== undefined) {
          setData(live);
        }
      } catch (e) {
        // Fallback to pre-indexed deterministic data
      }
    }
    loadInitial();
  }, []);

  const handleApplyPortfolio = async (
    weights: Record<string, number>,
    name: string
  ) => {
    setLoading(true);
    setErrorMessage(null);

    try {
      const live = await calculateRisk(weights);
      if (live && live.score !== undefined) {
        setData(live);
        setPortfolioName(name);
      }
    } catch (err: any) {
      setErrorMessage(err?.message || "Failed to calculate risk analysis for portfolio");
    } finally {
      setLoading(false);
      setActiveTab("overview");
    }
  };

  const handleSimulate = async (newWeights: Record<string, number>) => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const live = await calculateRisk(newWeights);
      if (live && live.score !== undefined) {
        setData(live);
      }
    } catch (e: any) {
      setErrorMessage(e?.message || "Failed to simulate custom stress scenario");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell
      activeTab={activeTab}
      onSelectTab={setActiveTab}
      portfolioName={portfolioName}
      walletAddress={connectedAddress}
      onNewPortfolio={() => setBuilderModalOpen(true)}
      onOpenWalletModal={() => setWalletModalOpen(true)}
    >
      {/* Request Error Alert Banner */}
      {errorMessage && (
        <div className="mb-6 flex items-center justify-between rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-xs text-rose-400 shadow-sm animate-in fade-in duration-150">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-rose-300">Request Error:</span>
            <span>{errorMessage}</span>
          </div>
          <button
            type="button"
            onClick={() => setErrorMessage(null)}
            className="ml-4 rounded px-1.5 py-0.5 text-xs text-rose-400 hover:bg-rose-500/20 hover:text-rose-200 transition"
            aria-label="Dismiss error"
          >
            ✕
          </button>
        </div>
      )}

      {/* Dynamic Tab Views */}
      {activeTab === "overview" && (
        <OverviewView data={data} onNavigateTab={setActiveTab} />
      )}

      {activeTab === "exposure" && <ExposureView data={data} />}

      {activeTab === "correlation" && <CorrelationView data={data} />}

      {activeTab === "stress" && (
        <StressView data={data} onSimulate={handleSimulate} />
      )}

      {activeTab === "report" && <ReportView data={data} />}

      {activeTab === "docs" && <DocsProofView />}

      {/* Manual Builder / Preset Selector Modal */}
      <PortfolioBuilderModal
        isOpen={builderModalOpen}
        onClose={() => setBuilderModalOpen(false)}
        onApplyPortfolio={handleApplyPortfolio}
      />

      {/* Dedicated Web3 Base Wallet Connect Modal */}
      <WalletConnectModal
        isOpen={walletModalOpen}
        onClose={() => setWalletModalOpen(false)}
        isConnected={isConnected}
        connectedAddress={connectedAddress}
        onConnectBrowser={connectBrowserWallet}
        onDisconnect={disconnectWallet}
        onSelectPortfolio={handleApplyPortfolio}
        hasProvider={hasProvider}
      />
    </AppShell>
  );
}

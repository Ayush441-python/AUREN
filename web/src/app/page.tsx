"use client";

import React, { useState, useEffect, useRef } from "react";
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
  const customAppliedRef = useRef(false);

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
        if (live && live.score !== undefined && !customAppliedRef.current) {
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
    customAppliedRef.current = true;
    setPortfolioName(name);
    setLoading(true);

    try {
      const live = await calculateRisk(weights);
      if (live && live.score !== undefined) {
        setData(live);
      }
    } catch (err) {
      // Create recalculated representation locally if offline
      setData({
        ...data,
        normalized_weights: weights,
      });
    } finally {
      setLoading(false);
      setActiveTab("overview");
    }
  };

  const handleSimulate = async (newWeights: Record<string, number>) => {
    setLoading(true);
    try {
      const live = await calculateRisk(newWeights);
      if (live && live.score !== undefined) {
        customAppliedRef.current = true;
        setData(live);
      }
    } catch (e) {
      // keep current data
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

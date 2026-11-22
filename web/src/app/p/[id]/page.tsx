"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/shell/AppShell";
import { NavTab } from "@/components/shell/Sidebar";
import { BASE_PORTFOLIO_ANALYSIS } from "@/lib/mock";
import { OverviewView } from "@/components/views/OverviewView";
import { ExposureView } from "@/components/views/ExposureView";
import { CorrelationView } from "@/components/views/CorrelationView";
import { StressView } from "@/components/views/StressView";
import { ReportView } from "@/components/views/ReportView";
import { DocsProofView } from "@/components/views/DocsProofView";
import { PortfolioBuilderModal } from "@/components/modals/PortfolioBuilderModal";
import { useParams } from "next/navigation";

export default function PortfolioDetailPage() {
  const params = useParams();
  const id = params?.id as string;
  const [activeTab, setActiveTab] = useState<NavTab>("overview");
  const [builderModalOpen, setBuilderModalOpen] = useState(false);

  return (
    <AppShell
      activeTab={activeTab}
      onSelectTab={setActiveTab}
      portfolioName={`Portfolio: ${id || "Analysis"}`}
      onNewPortfolio={() => setBuilderModalOpen(true)}
      onOpenWalletModal={() => setBuilderModalOpen(true)}
    >
      {activeTab === "overview" && (
        <OverviewView data={BASE_PORTFOLIO_ANALYSIS} onNavigateTab={setActiveTab} />
      )}
      {activeTab === "exposure" && <ExposureView data={BASE_PORTFOLIO_ANALYSIS} />}
      {activeTab === "correlation" && <CorrelationView data={BASE_PORTFOLIO_ANALYSIS} />}
      {activeTab === "stress" && <StressView data={BASE_PORTFOLIO_ANALYSIS} />}
      {activeTab === "report" && <ReportView data={BASE_PORTFOLIO_ANALYSIS} />}
      {activeTab === "docs" && <DocsProofView />}

      <PortfolioBuilderModal
        isOpen={builderModalOpen}
        onClose={() => setBuilderModalOpen(false)}
        onApplyPortfolio={() => setBuilderModalOpen(false)}
      />
    </AppShell>
  );
}

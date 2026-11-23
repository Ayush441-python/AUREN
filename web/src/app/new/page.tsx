"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/shell/AppShell";
import { PortfolioBuilderModal } from "@/components/modals/PortfolioBuilderModal";
import { useRouter } from "next/navigation";

export default function NewPortfolioPage() {
  const router = useRouter();
  const [modalOpen, setModalOpen] = useState(true);

  return (
    <AppShell activeTab="overview">
      <div className="flex h-96 items-center justify-center">
        <PortfolioBuilderModal
          isOpen={modalOpen}
          onClose={() => router.push("/")}
          onApplyPortfolio={(holdings, name) => {
            router.push("/");
          }}
        />
      </div>
    </AppShell>
  );
}

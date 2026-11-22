"use client";

import React from "react";
import { AppShell } from "@/components/shell/AppShell";
import { DocsProofView } from "@/components/views/DocsProofView";

export default function ApiDocsPage() {
  return (
    <AppShell activeTab="docs">
      <DocsProofView />
    </AppShell>
  );
}

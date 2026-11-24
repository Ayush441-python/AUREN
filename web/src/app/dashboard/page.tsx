import type { Metadata } from "next";
import { Workstation } from "@/components/dashboard/Workstation";
import type { DashboardTab } from "@/components/dashboard/Workstation";

export const metadata: Metadata = {
  title: "Workstation",
  description: "AUREN portfolio risk intelligence workstation.",
};

const tabs: DashboardTab[] = [
  "overview",
  "exposure",
  "correlation",
  "stress",
  "report",
  "docs",
];

function parseTab(value: string | string[] | undefined): DashboardTab {
  if (typeof value === "string" && tabs.includes(value as DashboardTab)) {
    return value as DashboardTab;
  }
  return "overview";
}

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await searchParams;

  return (
    <Workstation
      initialTab={parseTab(params.tab)}
      openBuilder={params.new === "1"}
      portfolioId={typeof params.portfolio === "string" ? params.portfolio : undefined}
    />
  );
}

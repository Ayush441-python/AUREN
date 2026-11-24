"use client";

import React, { useState } from "react";
import { RiskAnalysis, AIReportResponse } from "@/lib/types";
import { generateAIReport } from "@/lib/api";
import { Sparkles, CheckCircle2, AlertCircle, Copy, Check, RefreshCw, FileText } from "lucide-react";

interface Props {
  analysis: RiskAnalysis;
}

export function AIReportTab({ analysis }: Props) {
  const [reportData, setReportData] = useState<AIReportResponse | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setErrorMsg(null);
    try {
      const res = await generateAIReport(analysis);
      setReportData(res);
    } catch (err: unknown) {
      setErrorMsg(
        (err instanceof Error ? err.message : null) ||
          "Could not generate report. Ensure LLM_API_KEY is configured on the backend."
      );
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = () => {
    if (!reportData?.report) return;
    navigator.clipboard.writeText(reportData.report);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Top Controls Box */}
      <div className="rounded-xl border border-[#1f232c] bg-[#111318] p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-[#d8af3f]" />
            <span>AI Risk Narrative & Verification Auditor</span>
          </h3>
          <p className="text-[11px] text-zinc-400 mt-0.5">
            The mathematical engine computes the metrics; the language model solely articulates them.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {reportData && (
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 text-xs font-medium px-3 py-2 rounded-xl border border-[#1f232c] bg-[#161920] text-zinc-300 hover:text-white"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied" : "Copy Narrative"}</span>
            </button>
          )}

          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider px-4 py-2.5 rounded-xl bg-[#d8af3f] text-[#090a0d] hover:bg-[#e0b94c] transition-colors disabled:opacity-50"
          >
            {isGenerating ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Auditing Metrics & Writing...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>{reportData ? "Regenerate Report" : "Generate AI Report"}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl border border-rose-500/20 bg-rose-500/10 text-xs text-rose-300 flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Verification Status Pill */}
      {reportData && (
        <div
          className={`p-3.5 rounded-xl border flex items-center justify-between text-xs ${
            reportData.unverified_numbers.length === 0
              ? "border-emerald-500/20 bg-emerald-500/5 text-emerald-400"
              : "border-amber-500/20 bg-amber-500/5 text-amber-400"
          }`}
        >
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            <span>
              {reportData.unverified_numbers.length === 0
                ? "Mathematical Integrity Verified: 100% of figures cited in the text match deterministic metrics JSON."
                : `Caution: ${reportData.unverified_numbers.length} unverified number(s) detected in the model output.`}
            </span>
          </div>
          <span className="font-mono text-[10px] text-zinc-400">
            Model: {reportData.model}
          </span>
        </div>
      )}

      {/* Report Content */}
      {reportData ? (
        <div className="rounded-xl border border-[#1f232c] bg-[#111318] p-6 text-zinc-200 text-xs leading-relaxed font-sans whitespace-pre-line">
          {reportData.report}
        </div>
      ) : (
        <div className="p-12 text-center rounded-xl border border-[#1f232c] bg-[#111318]">
          <FileText className="w-8 h-8 text-zinc-600 mx-auto mb-2.5" />
          <p className="text-xs text-zinc-400">
            Click &quot;Generate AI Report&quot; to synthesize your portfolio risks into transparent plain English.
          </p>
        </div>
      )}
    </div>
  );
}

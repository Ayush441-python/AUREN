"use client";

import React, { useState } from "react";
import {
  X,
  Wallet,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ExternalLink,
  Copy,
  Check,
  Shield,
  Compass,
} from "lucide-react";
import { inspectWallet } from "@/lib/api";

interface WalletConnectModalProps {
  isOpen: boolean;
  onClose: () => void;
  isConnected: boolean;
  connectedAddress: string | null;
  onConnectBrowser: () => Promise<string | null>;
  onDisconnect: () => void;
  onSelectPortfolio: (weights: Record<string, number>, label: string) => void;
  hasProvider: boolean;
}

// Sample verified Base addresses with active balances for instant test
const DEMO_BASE_WALLETS = [
  {
    label: "Base Ecosystem Multi-Asset",
    address: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", // Native USDC on Base
  },
  {
    label: "Base High-Activity Trader",
    address: "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", // Vitalik demo
  },
];

export function WalletConnectModal({
  isOpen,
  onClose,
  isConnected,
  connectedAddress,
  onConnectBrowser,
  onDisconnect,
  onSelectPortfolio,
  hasProvider,
}: WalletConnectModalProps) {
  const [manualAddress, setManualAddress] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleBrowserConnect = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const addr = await onConnectBrowser();
      if (addr) {
        // Inspect wallet immediately
        const res = await inspectWallet(addr);
        if (res.has_holdings && Object.keys(res.portfolio).length > 0) {
          onSelectPortfolio(res.portfolio, `Base Wallet (${addr.slice(0, 6)}...${addr.slice(-4)})`);
          onClose();
        } else {
          // Normal wallet with 0 tokenized stocks: keep dialog open and show explanation
          setErrorMsg(res.message || "No supported assets in this wallet.");
        }
      }
    } catch (e: any) {
      setErrorMsg(e?.message || "Failed to connect to wallet.");
    } finally {
      setLoading(false);
    }
  };

  const handleManualInspect = async (addressToUse?: string) => {
    const target = (addressToUse || manualAddress).trim();
    if (!target) {
      setErrorMsg("Please enter a valid Base address (0x...)");
      return;
    }

    setLoading(true);
    setErrorMsg(null);

    try {
      const res = await inspectWallet(target);
      if (res.has_holdings && Object.keys(res.portfolio).length > 0) {
        onSelectPortfolio(res.portfolio, `Base: ${target.slice(0, 6)}...${target.slice(-4)}`);
        onClose();
      } else {
        setErrorMsg(
          res.message || "No supported assets detected in this address. Try an institutional preset or another address."
        );
      }
    } catch (err: any) {
      setErrorMsg(err?.message || "Error inspecting Base RPC.");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (connectedAddress) {
      navigator.clipboard.writeText(connectedAddress);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="flex w-full max-w-md flex-col rounded-xl border border-[#26262C] bg-[#151518] shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#26262C] px-5 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-[#E3B341]/10 text-[#E3B341] border border-[#E3B341]/20">
              <Wallet className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-[#F5F6F7]">Connect Base Wallet</h2>
              <p className="text-[11px] text-[#A1A4AB]">Direct on-chain portfolio telemetry via Base L2</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-[#A1A4AB] hover:bg-[#1C1C21] hover:text-[#F5F6F7]"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 space-y-4">
          {isConnected && connectedAddress ? (
            /* Active Connected State */
            <div className="rounded-lg border border-[#26262C] bg-[#1C1C21] p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-xs text-[#7FB3A6] font-medium">
                  <span className="h-2 w-2 rounded-full bg-[#7FB3A6] animate-pulse" />
                  <span>Wallet Connected</span>
                </span>
                <span className="rounded bg-[#0E0E10] px-2 py-0.5 font-mono text-[10px] text-[#A1A4AB] border border-[#26262C]">
                  Base Mainnet (8453)
                </span>
              </div>

              <div className="flex items-center justify-between rounded-md bg-[#0E0E10] p-2.5 border border-[#26262C]">
                <span className="font-mono text-xs text-[#F5F6F7] truncate max-w-[240px]">
                  {connectedAddress}
                </span>
                <button
                  onClick={handleCopy}
                  className="p-1 text-[#A1A4AB] hover:text-[#F5F6F7]"
                  title="Copy address"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-[#7FB3A6]" /> : <Copy className="h-3.5 w-3.5" />}
                </button>
              </div>

              <div className="flex gap-2 pt-1">
                <button
                  onClick={() => handleManualInspect(connectedAddress)}
                  disabled={loading}
                  className="flex-1 rounded-md bg-[#E3B341] py-2 text-xs font-semibold text-[#0E0E10] hover:bg-[#f0c254] flex items-center justify-center gap-2"
                >
                  {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                  <span>Sync Holdings</span>
                </button>
                <button
                  onClick={onDisconnect}
                  className="rounded-md border border-[#26262C] bg-[#151518] px-3 py-2 text-xs font-medium text-[#E07A5F] hover:bg-[#201c1c]"
                >
                  Disconnect
                </button>
              </div>
            </div>
          ) : (
            /* Connect Options */
            <div className="space-y-3">
              {/* Option 1: Browser Extension (MetaMask / Coinbase / Rainbow) */}
              <button
                onClick={handleBrowserConnect}
                disabled={loading}
                className="group flex w-full items-center justify-between rounded-lg border border-[#26262C] bg-[#1C1C21] p-3.5 text-left transition hover:border-[#E3B341] hover:bg-[#202026]"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-md bg-[#E3B341]/10 text-[#E3B341]">
                    <Wallet className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-[#F5F6F7] group-hover:text-[#E3B341]">
                      Browser Wallet
                    </div>
                    <div className="text-[11px] text-[#A1A4AB]">
                      {hasProvider
                        ? "MetaMask, Coinbase Wallet, Rainbow detected"
                        : "Detects installed EVM extension"}
                    </div>
                  </div>
                </div>
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin text-[#E3B341]" />
                ) : (
                  <span className="rounded bg-[#0E0E10] px-2 py-1 font-mono text-[10px] text-[#E3B341] border border-[#26262C]">
                    1-Click Connect
                  </span>
                )}
              </button>

              <div className="relative flex py-2 items-center">
                <div className="flex-grow border-t border-[#26262C]"></div>
                <span className="shrink-0 px-2 text-[10px] uppercase tracking-wider text-[#6B6E76]">
                  or inspect public address
                </span>
                <div className="flex-grow border-t border-[#26262C]"></div>
              </div>

              {/* Option 2: Enter Any Base Address Manually */}
              <div className="space-y-2">
                <label className="text-xs font-medium text-[#A1A4AB] block">
                  Public Base EVM Address
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="0x..."
                    value={manualAddress}
                    onChange={(e) => setManualAddress(e.target.value)}
                    className="flex-1 rounded-md border border-[#26262C] bg-[#0E0E10] px-3 py-2 font-mono text-xs text-[#F5F6F7] placeholder-[#6B6E76] focus:border-[#E3B341] focus:outline-hidden"
                  />
                  <button
                    onClick={() => handleManualInspect()}
                    disabled={loading}
                    className="rounded-md bg-[#E3B341] px-3.5 py-2 text-xs font-semibold text-[#0E0E10] hover:bg-[#f0c254] disabled:opacity-50 flex items-center gap-1.5"
                  >
                    {loading && <Loader2 className="h-3 w-3 animate-spin" />}
                    <span>Load</span>
                  </button>
                </div>
              </div>

              {/* Quick Demo Wallets */}
              <div className="pt-2">
                <span className="text-[11px] text-[#6B6E76] block mb-1.5">
                  Try sample Base address:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {DEMO_BASE_WALLETS.map((demo) => (
                    <button
                      key={demo.label}
                      onClick={() => {
                        setManualAddress(demo.address);
                        handleManualInspect(demo.address);
                      }}
                      className="rounded bg-[#1C1C21] px-2 py-1 text-[10px] text-[#A1A4AB] hover:text-[#F5F6F7] hover:bg-[#26262C] border border-[#26262C] font-mono"
                    >
                      {demo.label} ({demo.address.slice(0, 4)}...{demo.address.slice(-3)})
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {errorMsg && (
            <div className="rounded-md border border-[#E07A5F]/30 bg-[#E07A5F]/10 p-3 text-xs text-[#E07A5F] flex items-start gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Security & RPC Note */}
          <div className="rounded-md bg-[#0E0E10] p-3 border border-[#26262C] text-[11px] text-[#6B6E76] flex items-start gap-2">
            <Shield className="h-3.5 w-3.5 shrink-0 text-[#7FB3A6] mt-0.5" />
            <span>
              Read-only on-chain telemetry. AUREN never requests private keys or transaction approvals.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

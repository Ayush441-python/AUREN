"use client";

import { useState } from "react";
import {
  AlertCircle,
  Check,
  CheckCircle2,
  Copy,
  Loader2,
  LogOut,
  Shield,
  Wallet,
} from "lucide-react";
import { inspectWallet } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";

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

function shortAddress(address: string): string {
  if (address.length <= 14) return address;
  return `${address.slice(0, 8)}...${address.slice(-6)}`;
}

function message(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback;
}

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
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const applyInspectedWallet = async (address: string, labelPrefix: string) => {
    const response = await inspectWallet(address);
    if (response.has_holdings && Object.keys(response.portfolio).length > 0) {
      onSelectPortfolio(
        response.portfolio,
        `${labelPrefix} (${shortAddress(address)})`
      );
      onClose();
      return;
    }
    setErrorMessage(
      response.message || "No supported holdings were found at this address."
    );
  };

  const connectBrowser = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const address = await onConnectBrowser();
      if (!address) {
        setErrorMessage("No wallet address was returned by the browser provider.");
        return;
      }
      await applyInspectedWallet(address, "Base Wallet");
    } catch (error) {
      setErrorMessage(message(error, "Wallet connection failed."));
    } finally {
      setLoading(false);
    }
  };

  const inspectManual = async (addressOverride?: string) => {
    const target = (addressOverride ?? manualAddress).trim();
    if (!target) {
      setErrorMessage("Enter a public Base EVM address.");
      return;
    }
    setLoading(true);
    setErrorMessage(null);
    try {
      await applyInspectedWallet(target, "Base");
    } catch (error) {
      setErrorMessage(message(error, "The wallet service did not respond."));
    } finally {
      setLoading(false);
    }
  };

  const copyAddress = async () => {
    if (!connectedAddress) return;
    try {
      await navigator.clipboard.writeText(connectedAddress);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  };

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      title="Connect wallet"
      description="Read-only EVM wallet inspection. AUREN requests no signatures and never needs private keys."
      size="md"
    >
      <div className="space-y-5">
        {isConnected && connectedAddress ? (
          <div className="border border-line bg-obsidian/50 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="flex items-center gap-2 font-mono text-[0.62rem] uppercase tracking-[0.16em] text-positive">
                <CheckCircle2 aria-hidden="true" className="h-3.5 w-3.5" />
                Wallet connected
              </p>
              <span className="border border-line bg-secondary px-2 py-1 font-mono text-[0.58rem] uppercase tracking-[0.14em] text-faint">
                Base mainnet
              </span>
            </div>
            <div className="mt-4 flex items-center justify-between gap-3 border border-line bg-secondary px-3 py-2.5">
              <span className="min-w-0 truncate font-mono text-xs text-primary" title={connectedAddress}>
                {connectedAddress}
              </span>
              <button
                type="button"
                onClick={copyAddress}
                aria-label="Copy wallet address"
                className="shrink-0 border border-line p-1.5 text-muted transition-colors hover:border-gold/50 hover:text-champagne"
              >
                {copied ? (
                  <Check aria-hidden="true" className="h-3.5 w-3.5 text-positive" />
                ) : (
                  <Copy aria-hidden="true" className="h-3.5 w-3.5" />
                )}
              </button>
            </div>
            <span aria-live="polite" className="sr-only">
              {copied ? "Wallet address copied" : ""}
            </span>
            <div className="mt-4 flex flex-col gap-3 sm:flex-row">
              <Button
                variant="primary"
                onClick={() => inspectManual(connectedAddress)}
                disabled={loading}
                className="flex-1"
              >
                {loading ? (
                  <Loader2 aria-hidden="true" className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Wallet aria-hidden="true" className="h-3.5 w-3.5" />
                )}
                Sync holdings
              </Button>
              <Button variant="secondary" onClick={onDisconnect} className="shrink-0">
                <LogOut aria-hidden="true" className="h-3.5 w-3.5" />
                Disconnect
              </Button>
            </div>
          </div>
        ) : (
          <>
            <button
              type="button"
              onClick={connectBrowser}
              disabled={loading}
              className="group flex w-full items-center justify-between gap-4 border border-line bg-obsidian/50 px-4 py-4 text-left transition-colors hover:border-gold/50 hover:bg-gold/[0.04]"
            >
              <span className="flex items-center gap-3">
                <span className="border border-gold/30 bg-gold/10 p-2 text-champagne">
                  <Wallet aria-hidden="true" className="h-4 w-4" />
                </span>
                <span>
                  <span className="block text-sm text-primary group-hover:text-highlight">
                    Browser wallet
                  </span>
                  <span className="mt-1 block text-xs text-muted">
                    {hasProvider
                      ? "An EVM provider was detected in this browser."
                      : "No injected provider detected. Use a public address instead."}
                  </span>
                </span>
              </span>
              {loading ? (
                <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin text-champagne" />
              ) : (
                <span className="font-mono text-[0.58rem] uppercase tracking-[0.14em] text-faint group-hover:text-champagne">
                  Connect
                </span>
              )}
            </button>

            <div className="flex items-center gap-3">
              <span aria-hidden="true" className="h-px flex-1 bg-line" />
              <span className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-faint">
                or inspect a public address
              </span>
              <span aria-hidden="true" className="h-px flex-1 bg-line" />
            </div>

            <div>
              <label htmlFor="wallet-address" className="auren-eyebrow">
                Base EVM address
              </label>
              <div className="mt-2 flex flex-col gap-3 sm:flex-row">
                <input
                  id="wallet-address"
                  type="text"
                  value={manualAddress}
                  onChange={(event) => setManualAddress(event.target.value)}
                  placeholder="0x..."
                  autoComplete="off"
                  className="min-w-0 flex-1 border border-line bg-obsidian px-3 py-2.5 font-mono text-xs text-primary placeholder:text-faint focus:border-gold/60 focus:outline-none"
                />
                <Button variant="primary" onClick={() => inspectManual()} disabled={loading} className="shrink-0">
                  {loading ? (
                    <Loader2 aria-hidden="true" className="h-3.5 w-3.5 animate-spin" />
                  ) : null}
                  Load
                </Button>
              </div>
            </div>
          </>
        )}

        {errorMessage && (
          <p role="alert" className="flex items-start gap-2 border border-negative/30 bg-negative/5 px-4 py-3 text-xs leading-relaxed text-primary">
            <AlertCircle aria-hidden="true" className="mt-0.5 h-3.5 w-3.5 shrink-0 text-negative" />
            {errorMessage}
          </p>
        )}

        <div className="flex items-start gap-2 border-l border-positive/50 pl-3 text-xs leading-relaxed text-faint">
          <Shield aria-hidden="true" className="mt-0.5 h-3.5 w-3.5 shrink-0 text-positive" />
          Read-only inspection. Supported holdings are converted to weights and recalculated by the risk engine.
        </div>
      </div>
    </Dialog>
  );
}

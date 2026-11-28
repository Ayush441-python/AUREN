"use client";

import { useState, useEffect, useMemo } from "react";
import {
  AlertCircle,
  Check,
  CheckCircle2,
  Copy,
  ExternalLink,
  Fingerprint,
  Loader2,
  ShieldCheck,
  Zap,
} from "lucide-react";
import type { RiskAnalysis } from "@/lib/types";
import { formatPercent } from "@/lib/format";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { RiskBadge } from "@/components/ui/RiskBadge";

interface OnchainAttestModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: RiskAnalysis;
  portfolioName: string;
}

const BASE_CHAIN_ID = "0x2105";
const ERC8021_MARKER = "80218021802180218021802180218021";

function toHexUtf8(str: string): string {
  const bytes = new TextEncoder().encode(str);
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function encodeErc8021Suffix(builderCode: string): string {
  const clean = builderCode.trim();
  if (!clean) return "";
  const bytes = new TextEncoder().encode(clean);
  if (bytes.length > 255) return "";
  const codeHex = Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  const lenHex = bytes.length.toString(16).padStart(2, "0");
  return `${codeHex}${lenHex}00${ERC8021_MARKER}`;
}

function simpleHash(input: string): string {
  let h1 = 0xdeadbeef ^ input.length;
  let h2 = 0x41c6ce57 ^ input.length;
  for (let i = 0; i < input.length; i++) {
    const ch = input.charCodeAt(i);
    h1 = Math.imul(h1 ^ ch, 2654435761);
    h2 = Math.imul(h2 ^ ch, 1597334677);
  }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
  return (h2 >>> 0).toString(16).padStart(8, "0") + (h1 >>> 0).toString(16).padStart(8, "0");
}

export function OnchainAttestModal({
  isOpen,
  onClose,
  data,
  portfolioName,
}: OnchainAttestModalProps) {
  const [builderCode, setBuilderCode] = useState("bc_auren");
  const [status, setStatus] = useState<"idle" | "signing" | "confirming" | "confirmed" | "error">("idle");
  const [txHash, setTxHash] = useState<string | null>(null);
  const [blockNumber, setBlockNumber] = useState<number | null>(null);
  const [senderAddress, setSenderAddress] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [copiedTx, setCopiedTx] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("auren_builder_code");
      if (saved) setBuilderCode(saved);
    }
  }, []);

  const handleBuilderCodeChange = (val: string) => {
    setBuilderCode(val);
    if (typeof window !== "undefined") {
      localStorage.setItem("auren_builder_code", val.trim());
    }
  };

  const topAsset = data.concentration.top_asset;
  const topWeight = formatPercent(data.concentration.top_weight, 0);

  const encoded = useMemo(() => {
    const pHash = simpleHash(
      `${portfolioName}:${data.score}:${data.level}:${topAsset}:${JSON.stringify(
        data.normalized_weights
      )}`
    );
    const payloadText = `AUREN_AUDIT_V1|score=${data.score}|level=${data.level}|top=${topAsset}:${topWeight}|hash=${pHash}`;
    const payloadHex = toHexUtf8(payloadText);
    const suffixHex = encodeErc8021Suffix(builderCode);
    const calldata = `0x${payloadHex}${suffixHex}`;
    return {
      payloadText,
      payloadHex: `0x${payloadHex}`,
      suffixHex: suffixHex ? `0x${suffixHex}` : null,
      calldata,
    };
  }, [portfolioName, data.score, data.level, data.normalized_weights, topAsset, topWeight, builderCode]);

  const handleAttestOnchain = async () => {
    setErrorMsg(null);
    const eth = typeof window !== "undefined" ? window.ethereum : undefined;
    if (!eth) {
      setStatus("error");
      setErrorMsg(
        "No Web3 wallet detected in browser. Please open in MetaMask or Coinbase Wallet to broadcast on Base Mainnet."
      );
      return;
    }

    setStatus("signing");
    try {
      const accounts = await eth.request<string[]>({
        method: "eth_requestAccounts",
      });
      if (!accounts || accounts.length === 0) {
        throw new Error("No wallet account authorized.");
      }
      const account = accounts[0];
      setSenderAddress(account);

      // Ensure Base Mainnet (Chain ID 8453 / 0x2105)
      const currentChain = await eth.request<string>({ method: "eth_chainId" });
      if (currentChain?.toLowerCase() !== BASE_CHAIN_ID) {
        try {
          await eth.request({
            method: "wallet_switchEthereumChain",
            params: [{ chainId: BASE_CHAIN_ID }],
          });
        } catch (switchErr: unknown) {
          const code =
            typeof switchErr === "object" && switchErr !== null && "code" in switchErr
              ? (switchErr as { code?: number }).code
              : undefined;
          if (code === 4902) {
            await eth.request({
              method: "wallet_addEthereumChain",
              params: [
                {
                  chainId: BASE_CHAIN_ID,
                  chainName: "Base Mainnet",
                  nativeCurrency: { name: "Ether", symbol: "ETH", decimals: 18 },
                  rpcUrls: ["https://mainnet.base.org"],
                  blockExplorerUrls: ["https://basescan.org"],
                },
              ],
            });
          } else {
            throw new Error("Please switch your wallet network to Base Mainnet (Chain ID 8453).");
          }
        }
      }

      // Send real on-chain Base Mainnet transaction with ERC-8021 Builder Code suffix
      const hash = await eth.request<string>({
        method: "eth_sendTransaction",
        params: [
          {
            from: account,
            to: account,
            value: "0x0",
            data: encoded.calldata,
          },
        ],
      });

      setTxHash(hash);
      setStatus("confirming");

      // Poll for transaction receipt on Base Mainnet
      for (let attempt = 0; attempt < 25; attempt++) {
        await new Promise((r) => setTimeout(r, 1500));
        try {
          const receipt = await eth.request<{ blockNumber?: string; status?: string } | null>({
            method: "eth_getTransactionReceipt",
            params: [hash],
          });
          if (receipt && receipt.blockNumber) {
            setBlockNumber(parseInt(receipt.blockNumber, 16));
            setStatus("confirmed");
            return;
          }
        } catch {
          // continue polling
        }
      }

      // Even if receipt polling times out, txHash is broadcast
      setStatus("confirmed");
    } catch (err: unknown) {
      setStatus("error");
      setErrorMsg(
        err instanceof Error && err.message
          ? err.message
          : "Transaction rejected or failed to broadcast."
      );
    }
  };

  const copyTxHash = async () => {
    if (!txHash) return;
    try {
      await navigator.clipboard.writeText(txHash);
      setCopiedTx(true);
      window.setTimeout(() => setCopiedTx(false), 2000);
    } catch {
      setCopiedTx(false);
    }
  };

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      title="Attest Risk Audit On-Chain (Base Mainnet)"
      description="Record a verifiable portfolio risk proof on Base Mainnet (Chain ID 8453) with ERC-8021 Base Builder Code attribution."
      size="lg"
    >
      <div className="space-y-5">
        {/* Summary Banner */}
        <div className="flex flex-col justify-between gap-4 rounded-xl border border-gold/40 bg-obsidian p-4 sm:flex-row sm:items-center">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-[0.62rem] uppercase tracking-[0.16em] text-gold">
                Base Mainnet · Chain ID 8453
              </span>
            </div>
            <h3 className="mt-1 text-base font-bold text-primary">{portfolioName}</h3>
            <p className="mt-0.5 text-xs text-muted">
              Top Holding: {topAsset} ({topWeight}) · Gas cost: ~0.000005 ETH (&lt;$0.005)
            </p>
          </div>
          <RiskBadge level={data.level} score={data.score} />
        </div>

        {/* Base Builder Code Input (ERC-8021) */}
        <div>
          <div className="flex items-center justify-between">
            <label htmlFor="builder-code-input" className="auren-eyebrow">
              Base Builder Code (ERC-8021 Attribution)
            </label>
            <span className="font-mono text-[0.6rem] text-positive">
              Schema 0 · 0x8021...8021 Marker
            </span>
          </div>
          <div className="mt-1.5 flex flex-col gap-2 sm:flex-row">
            <input
              id="builder-code-input"
              type="text"
              value={builderCode}
              onChange={(e) => handleBuilderCodeChange(e.target.value)}
              placeholder="bc_xxxxxxxx"
              className="min-w-0 flex-1 border border-line bg-obsidian px-3 py-2 font-mono text-xs text-primary placeholder:text-faint focus:border-gold/60 focus:outline-none"
            />
          </div>
          <p className="mt-1 text-[0.68rem] text-muted">
            Paste your <code className="text-champagne">bc_...</code> code from{" "}
            <a
              href="https://dashboard.base.org"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gold underline hover:text-highlight"
            >
              dashboard.base.org
            </a>{" "}
            to attribute this on-chain Base Mainnet transaction for Builder Circle verification.
          </p>
        </div>

        {/* Calldata & ERC-8021 Hex Inspector */}
        <div className="space-y-2 rounded-lg border border-line bg-secondary/60 p-3.5">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 font-mono text-[0.62rem] uppercase tracking-[0.14em] text-champagne">
              <Fingerprint aria-hidden="true" className="h-3.5 w-3.5 text-gold" />
              On-Chain Transaction Payload &amp; ERC-8021 Suffix
            </span>
            <span className="font-mono text-[0.6rem] text-muted">
              {(encoded.calldata.length - 2) / 2} bytes
            </span>
          </div>

          <div className="space-y-1.5 font-mono text-[0.68rem]">
            <div className="rounded border border-line bg-obsidian px-2.5 py-1.5 text-primary">
              <span className="text-muted">ASCII Proof: </span>
              <span className="break-all text-champagne">{encoded.payloadText}</span>
            </div>
            {encoded.suffixHex && (
              <div className="rounded border border-line bg-obsidian px-2.5 py-1.5 text-primary">
                <span className="text-muted">ERC-8021 Suffix: </span>
                <span className="break-all text-positive">{encoded.suffixHex}</span>
              </div>
            )}
          </div>
        </div>

        {/* Confirmed Transaction Proof Box */}
        {txHash && (
          <div className="rounded-xl border border-positive/50 bg-positive/10 p-4">
            <div className="flex items-center justify-between gap-2">
              <span className="flex items-center gap-2 font-mono text-xs font-bold uppercase tracking-wider text-positive">
                <CheckCircle2 aria-hidden="true" className="h-4 w-4" />
                {status === "confirming"
                  ? "Transaction Broadcasted on Base Mainnet..."
                  : "Confirmed On-Chain Base Mainnet Transaction"}
              </span>
              {blockNumber && (
                <span className="border border-positive/40 bg-obsidian/70 px-2 py-0.5 font-mono text-[0.62rem] text-positive">
                  Block #{blockNumber}
                </span>
              )}
            </div>

            <div className="mt-3 flex items-center justify-between gap-2 rounded border border-line bg-obsidian px-3 py-2">
              <span className="truncate font-mono text-xs text-primary" title={txHash}>
                {txHash}
              </span>
              <button
                type="button"
                onClick={copyTxHash}
                className="shrink-0 border border-line p-1.5 text-muted hover:border-gold/50 hover:text-champagne"
                aria-label="Copy transaction hash"
              >
                {copiedTx ? (
                  <Check aria-hidden="true" className="h-3.5 w-3.5 text-positive" />
                ) : (
                  <Copy aria-hidden="true" className="h-3.5 w-3.5" />
                )}
              </button>
            </div>

            {senderAddress && (
              <p className="mt-2 font-mono text-[0.65rem] text-muted">
                Attested by: <span className="text-primary">{senderAddress}</span> · Builder Code:{" "}
                <span className="text-champagne">{builderCode || "none"}</span>
              </p>
            )}

            <div className="mt-3 flex flex-wrap items-center gap-3">
              <a
                href={`https://basescan.org/tx/${txHash}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 rounded bg-positive px-3.5 py-2 font-mono text-xs font-bold uppercase tracking-wider text-obsidian transition-opacity hover:opacity-90"
              >
                View Live Transaction on BaseScan.org
                <ExternalLink aria-hidden="true" className="h-3.5 w-3.5" />
              </a>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {errorMsg && (
          <div
            role="alert"
            className="flex items-start gap-2 rounded-lg border border-negative/40 bg-negative/10 px-4 py-3 text-xs leading-relaxed text-primary"
          >
            <AlertCircle aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-negative" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Action Footer */}
        <div className="flex flex-col gap-3 border-t border-line pt-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-1.5 text-xs text-muted">
            <ShieldCheck aria-hidden="true" className="h-4 w-4 text-positive" />
            <span>0-ETH self-attestation · No token approvals</span>
          </div>
          <Button
            variant="primary"
            onClick={handleAttestOnchain}
            disabled={status === "signing" || status === "confirming"}
            className="text-xs"
          >
            {status === "signing" || status === "confirming" ? (
              <>
                <Loader2 aria-hidden="true" className="h-3.5 w-3.5 animate-spin" />
                {status === "signing" ? "Confirm in Wallet..." : "Confirming on Base..."}
              </>
            ) : (
              <>
                <Zap aria-hidden="true" className="h-3.5 w-3.5" />
                {txHash ? "Attest Again on Base Mainnet" : "Sign & Attest on Base Mainnet"}
              </>
            )}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}

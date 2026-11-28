"use client";

import { useState } from "react";
import { ArrowRight, Loader2, Plus, Sparkles, Trash2, Wallet } from "lucide-react";
import { inspectWallet } from "@/lib/api";
import { BASE_STOCKS_DEMO_PRESET, PRESETS, type PresetPortfolio } from "@/lib/presets";
import { formatPercent } from "@/lib/format";
import { cn } from "@/lib/cn";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";

interface PortfolioBuilderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onApplyPortfolio: (holdings: Record<string, number>, name: string) => void;
}

type Mode = "presets" | "wallet" | "custom";
type CustomAsset = { ticker: string; weight: number };

const modes: { id: Mode; label: string }[] = [
  { id: "presets", label: "Presets" },
  { id: "wallet", label: "Wallet" },
  { id: "custom", label: "Custom" },
];

function normalizeAssets(assets: CustomAsset[]): Record<string, number> {
  const cleaned = assets
    .map((asset) => ({ ticker: asset.ticker.trim().toUpperCase(), weight: asset.weight }))
    .filter((asset) => asset.ticker && Number.isFinite(asset.weight) && asset.weight > 0);
  const total = cleaned.reduce((sum, asset) => sum + asset.weight, 0);
  return Object.fromEntries(cleaned.map((asset) => [asset.ticker, asset.weight / total]));
}

function presetWeights(preset: PresetPortfolio): Record<string, number> {
  const total = preset.holdings.reduce((sum, [, weight]) => sum + weight, 0);
  return Object.fromEntries(preset.holdings.map(([ticker, weight]) => [ticker, weight / total]));
}

export function PortfolioBuilderModal({
  isOpen,
  onClose,
  onApplyPortfolio,
}: PortfolioBuilderModalProps) {
  const [mode, setMode] = useState<Mode>("presets");
  const [address, setAddress] = useState("");
  const [walletLoading, setWalletLoading] = useState(false);
  const [walletError, setWalletError] = useState<string | null>(null);
  const [walletEmptyNotice, setWalletEmptyNotice] = useState<string | null>(null);
  const [assets, setAssets] = useState<CustomAsset[]>([
    { ticker: "NVDA", weight: 40 },
    { ticker: "MSFT", weight: 30 },
    { ticker: "ETH-USD", weight: 30 },
  ]);
  const [newTicker, setNewTicker] = useState("");

  const total = assets.reduce((sum, asset) => sum + (Number.isFinite(asset.weight) ? asset.weight : 0), 0);
  const normalizedAssets = normalizeAssets(assets);

  const applyPreset = (preset: PresetPortfolio) => {
    onApplyPortfolio(presetWeights(preset), preset.name);
    onClose();
  };

  const inspect = async () => {
    const trimmed = address.trim();
    if (!trimmed) {
      setWalletError("Enter a public Base EVM address.");
      setWalletEmptyNotice(null);
      return;
    }
    setWalletLoading(true);
    setWalletError(null);
    setWalletEmptyNotice(null);
    try {
      const response = await inspectWallet(trimmed);
      if (response.has_holdings && Object.keys(response.portfolio).length > 0) {
        const label = `Base Wallet (${trimmed.slice(0, 6)}...${trimmed.slice(-4)})`;
        onApplyPortfolio(response.portfolio, label);
        onClose();
      } else {
        setWalletEmptyNotice(
          response.message || "No tokenized stocks or major Base assets detected in this wallet yet."
        );
      }
    } catch (error) {
      setWalletError(
        error instanceof Error && error.message
          ? error.message
          : "The wallet service did not respond."
      );
    } finally {
      setWalletLoading(false);
    }
  };

  const applyCustom = () => {
    if (!Object.keys(normalizedAssets).length) return;
    onApplyPortfolio(normalizedAssets, "Custom Allocation");
    onClose();
  };

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      title="Load portfolio"
      description="Choose a preset, inspect a public wallet, or define an exact weight vector. All allocations are normalized before analysis."
      size="lg"
    >
      <div role="tablist" aria-label="Portfolio source" className="grid grid-cols-3 border border-line">
        {modes.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            id={`builder-tab-${item.id}`}
            aria-selected={mode === item.id}
            aria-controls={`builder-panel-${item.id}`}
            onClick={() => setMode(item.id)}
            className={cn(
              "px-3 py-3 font-mono text-[0.62rem] uppercase tracking-[0.16em] transition-colors",
              mode === item.id
                ? "bg-gold/10 text-highlight"
                : "bg-secondary/50 text-muted hover:text-primary"
            )}
          >
            {item.label}
          </button>
        ))}
      </div>

      <div className="mt-5">
        {mode === "presets" && (
          <div
            role="tabpanel"
            id="builder-panel-presets"
            aria-labelledby="builder-tab-presets"
            className="space-y-3"
          >
            {Object.values(PRESETS).map((preset) => {
              const weights = presetWeights(preset);
              return (
                <button
                  key={preset.name}
                  type="button"
                  onClick={() => applyPreset(preset)}
                  className="group flex w-full items-center justify-between gap-4 border border-line bg-obsidian/50 px-4 py-4 text-left transition-colors hover:border-gold/50 hover:bg-gold/[0.04]"
                >
                  <span className="min-w-0">
                    <span className="block text-sm text-primary group-hover:text-highlight">
                      {preset.name}
                    </span>
                    <span className="mt-1 block text-xs leading-relaxed text-muted">
                      {preset.description}
                    </span>
                    <span className="mt-2 flex flex-wrap gap-2">
                      {Object.entries(weights).map(([ticker, weight]) => (
                        <span
                          key={ticker}
                          className="border border-line bg-secondary px-2 py-1 font-mono text-[0.6rem] text-faint"
                        >
                          {ticker} {formatPercent(weight, 0)}
                        </span>
                      ))}
                    </span>
                  </span>
                  <ArrowRight aria-hidden="true" className="h-4 w-4 shrink-0 text-faint group-hover:text-champagne" />
                </button>
              );
            })}
          </div>
        )}

        {mode === "wallet" && (
          <div
            role="tabpanel"
            id="builder-panel-wallet"
            aria-labelledby="builder-tab-wallet"
            className="space-y-4"
          >
            <p className="text-xs leading-relaxed text-muted">
              A public EVM address is read only. The wallet endpoint checks supported tokenized
              assets and returns a normalized weight vector when holdings are detected.
            </p>
            <div>
              <label htmlFor="builder-address" className="auren-eyebrow">
                Public Base address
              </label>
              <div className="mt-2 flex flex-col gap-3 sm:flex-row">
                <input
                  id="builder-address"
                  type="text"
                  value={address}
                  onChange={(event) => setAddress(event.target.value)}
                  placeholder="0x..."
                  autoComplete="off"
                  className="min-w-0 flex-1 border border-line bg-obsidian px-3 py-2.5 font-mono text-xs text-primary placeholder:text-faint focus:border-gold/60 focus:outline-none"
                />
                <Button variant="primary" onClick={inspect} disabled={walletLoading} className="shrink-0">
                  {walletLoading ? (
                    <Loader2 aria-hidden="true" className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Wallet aria-hidden="true" className="h-3.5 w-3.5" />
                  )}
                  Inspect
                </Button>
              </div>
            </div>
            {walletEmptyNotice && (
              <div className="border border-gold/40 bg-gold/[0.06] px-4 py-4 text-xs leading-relaxed">
                <p className="text-primary">{walletEmptyNotice}</p>
                <p className="mt-1 text-muted">
                  Inspect a simulated Coinbase B20 tokenized stock and Base DeFi allocation with one click:
                </p>
                <div className="mt-3">
                  <Button
                    variant="primary"
                    onClick={() => applyPreset(BASE_STOCKS_DEMO_PRESET)}
                    className="w-full sm:w-auto"
                  >
                    <Sparkles aria-hidden="true" className="h-3.5 w-3.5" />
                    Load Base Stocks Demo Portfolio
                  </Button>
                </div>
              </div>
            )}
            {walletError && (
              <div role="alert" className="border border-negative/30 bg-negative/5 px-4 py-3 text-xs leading-relaxed text-primary">
                <p>{walletError}</p>
                <div className="mt-3">
                  <Button
                    variant="secondary"
                    onClick={() => applyPreset(BASE_STOCKS_DEMO_PRESET)}
                    className="text-xs"
                  >
                    <Sparkles aria-hidden="true" className="h-3.5 w-3.5 text-gold" />
                    Load Base Stocks Demo Portfolio Instead
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}

        {mode === "custom" && (
          <div
            role="tabpanel"
            id="builder-panel-custom"
            aria-labelledby="builder-tab-custom"
            className="space-y-4"
          >
            <div className="max-h-72 space-y-2 overflow-y-auto pr-1">
              {assets.map((asset, index) => (
                <div key={index} className="grid grid-cols-[minmax(0,1fr)_5rem_2rem] gap-2">
                  <label className="sr-only" htmlFor={`asset-ticker-${index}`}>
                    Asset ticker
                  </label>
                  <input
                    id={`asset-ticker-${index}`}
                    type="text"
                    value={asset.ticker}
                    onChange={(event) =>
                      setAssets((current) =>
                        current.map((item, itemIndex) =>
                          itemIndex === index
                            ? { ...item, ticker: event.target.value.toUpperCase() }
                            : item
                        )
                      )
                    }
                    placeholder="TICKER"
                    className="min-w-0 border border-line bg-obsidian px-3 py-2 font-mono text-xs text-primary placeholder:text-faint focus:border-gold/60 focus:outline-none"
                  />
                  <label className="sr-only" htmlFor={`asset-weight-${index}`}>
                    Asset weight percentage
                  </label>
                  <input
                    id={`asset-weight-${index}`}
                    type="number"
                    min={0}
                    max={100}
                    step={1}
                    value={asset.weight}
                    onChange={(event) =>
                      setAssets((current) =>
                        current.map((item, itemIndex) =>
                          itemIndex === index
                            ? { ...item, weight: Number(event.target.value) }
                            : item
                        )
                      )
                    }
                    className="border border-line bg-obsidian px-2 py-2 font-mono text-xs text-primary focus:border-gold/60 focus:outline-none"
                  />
                  <button
                    type="button"
                    aria-label={`Remove ${asset.ticker || `row ${index + 1}`}`}
                    onClick={() => setAssets((current) => current.filter((_, itemIndex) => itemIndex !== index))}
                    className="border border-line text-muted transition-colors hover:border-negative/50 hover:text-negative"
                  >
                    <Trash2 aria-hidden="true" className="mx-auto h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>

            <div className="flex flex-col gap-3 sm:flex-row">
              <label className="sr-only" htmlFor="new-ticker">
                New asset ticker
              </label>
              <input
                id="new-ticker"
                type="text"
                value={newTicker}
                onChange={(event) => setNewTicker(event.target.value.toUpperCase())}
                placeholder="Add ticker"
                className="min-w-0 flex-1 border border-line bg-obsidian px-3 py-2 font-mono text-xs text-primary placeholder:text-faint focus:border-gold/60 focus:outline-none"
              />
              <Button
                variant="secondary"
                onClick={() => {
                  const ticker = newTicker.trim();
                  if (!ticker) return;
                  setAssets((current) => [...current, { ticker, weight: 10 }]);
                  setNewTicker("");
                }}
                className="shrink-0"
              >
                <Plus aria-hidden="true" className="h-3.5 w-3.5" />
                Add asset
              </Button>
            </div>

            <div className="flex flex-col gap-3 border-t border-line pt-4 sm:flex-row sm:items-center sm:justify-between">
              <p aria-live="polite" className="font-mono text-xs text-muted">
                Raw total: <span className={cn(Math.abs(total - 100) < 1 ? "text-positive" : "text-champagne")}>{formatPercent(total / 100)}</span>
                <span className="ml-2 text-faint">→ normalized to 100%</span>
              </p>
              <Button variant="primary" onClick={applyCustom} disabled={!Object.keys(normalizedAssets).length}>
                Analyze custom portfolio
              </Button>
            </div>
          </div>
        )}
      </div>
    </Dialog>
  );
}

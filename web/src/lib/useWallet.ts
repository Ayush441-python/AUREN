"use client";

import { useState, useEffect, useCallback } from "react";

export interface WalletState {
  address: string | null;
  chainId: string | null;
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  hasProvider: boolean;
}

interface EthereumProvider {
  request<T = unknown>(args: { method: string; params?: unknown }): Promise<T>;
  on?(event: "accountsChanged", listener: (accounts: string[]) => void): void;
  on?(event: "chainChanged", listener: (chainId: string) => void): void;
  removeListener?(event: "accountsChanged", listener: (accounts: string[]) => void): void;
  removeListener?(event: "chainChanged", listener: (chainId: string) => void): void;
}

declare global {
  interface Window {
    ethereum?: EthereumProvider;
  }
}

const BASE_CHAIN_ID = "0x2105";

const getProvider = (): EthereumProvider | undefined =>
  typeof window === "undefined" ? undefined : window.ethereum;

function providerErrorCode(error: unknown): number | undefined {
  if (typeof error === "object" && error !== null && "code" in error) {
    const code = (error as { code?: unknown }).code;
    return typeof code === "number" ? code : undefined;
  }
  return undefined;
}

export function useWallet() {
  const [address, setAddress] = useState<string | null>(null);
  const [chainId, setChainId] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasProvider, setHasProvider] = useState(false);

  useEffect(() => {
    const eth = getProvider();
    if (!eth) return;

    let active = true;
    queueMicrotask(() => {
      if (active) setHasProvider(true);
    });

    eth
      .request<string[]>({ method: "eth_accounts" })
      .then((accounts) => {
        if (!active) return;
        if (accounts && accounts.length > 0) {
          setAddress(accounts[0]);
        }
      })
      .catch(() => {});

    eth
      .request<string>({ method: "eth_chainId" })
      .then((id) => {
        if (active) setChainId(id);
      })
      .catch(() => {});

    const handleAccountsChanged = (accounts: string[]) => {
      if (!active) return;
      if (accounts && accounts.length > 0) {
        setAddress(accounts[0]);
      } else {
        setAddress(null);
      }
    };

    const handleChainChanged = (id: string) => {
      if (active) setChainId(id);
    };

    eth.on?.("accountsChanged", handleAccountsChanged);
    eth.on?.("chainChanged", handleChainChanged);

    return () => {
      active = false;
      eth.removeListener?.("accountsChanged", handleAccountsChanged);
      eth.removeListener?.("chainChanged", handleChainChanged);
    };
  }, []);

  const connect = useCallback(async (): Promise<string | null> => {
    const eth = getProvider();
    if (!eth) {
      setError(
        "No Web3 wallet detected. Please install MetaMask or Coinbase Wallet, or paste your address manually."
      );
      return null;
    }

    setIsConnecting(true);
    setError(null);

    try {
      const accounts = await eth.request<string[]>({
        method: "eth_requestAccounts",
      });

      if (!accounts || accounts.length === 0) {
        throw new Error("No accounts authorized by user.");
      }

      const connectedAddress = accounts[0];
      setAddress(connectedAddress);

      try {
        await eth.request({
          method: "wallet_switchEthereumChain",
          params: [{ chainId: BASE_CHAIN_ID }],
        });
        setChainId(BASE_CHAIN_ID);
      } catch (switchError: unknown) {
        if (providerErrorCode(switchError) === 4902) {
          try {
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
            setChainId(BASE_CHAIN_ID);
          } catch (addError) {
            console.warn("User dismissed Base network addition", addError);
          }
        }
      }

      setIsConnecting(false);
      return connectedAddress;
    } catch (err: unknown) {
      setError((err instanceof Error ? err.message : null) || "User rejected connection request.");
      setIsConnecting(false);
      return null;
    }
  }, []);

  const disconnect = useCallback(() => {
    setAddress(null);
    setError(null);
  }, []);

  return {
    address,
    chainId,
    isConnected: !!address,
    isConnecting,
    error,
    hasProvider,
    connect,
    disconnect,
  };
}

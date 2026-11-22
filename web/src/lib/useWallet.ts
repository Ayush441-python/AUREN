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

const BASE_CHAIN_ID = "0x2105"; // 8453 in hex

export function useWallet() {
  const [address, setAddress] = useState<string | null>(null);
  const [chainId, setChainId] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasProvider, setHasProvider] = useState(false);

  // Check for window.ethereum on mount
  useEffect(() => {
    if (typeof window !== "undefined" && (window as any).ethereum) {
      setHasProvider(true);

      const eth = (window as any).ethereum;

      // Check if already authorized
      eth
        .request({ method: "eth_accounts" })
        .then((accounts: string[]) => {
          if (accounts && accounts.length > 0) {
            setAddress(accounts[0]);
          }
        })
        .catch(() => {});

      eth
        .request({ method: "eth_chainId" })
        .then((id: string) => {
          setChainId(id);
        })
        .catch(() => {});

      // Event listeners
      const handleAccountsChanged = (accounts: string[]) => {
        if (accounts && accounts.length > 0) {
          setAddress(accounts[0]);
        } else {
          setAddress(null);
        }
      };

      const handleChainChanged = (id: string) => {
        setChainId(id);
      };

      eth.on("accountsChanged", handleAccountsChanged);
      eth.on("chainChanged", handleChainChanged);

      return () => {
        if (eth.removeListener) {
          eth.removeListener("accountsChanged", handleAccountsChanged);
          eth.removeListener("chainChanged", handleChainChanged);
        }
      };
    }
  }, []);

  const connect = useCallback(async (): Promise<string | null> => {
    if (typeof window === "undefined" || !(window as any).ethereum) {
      setError("No Web3 wallet detected. Please install MetaMask or Coinbase Wallet, or paste your address manually.");
      return null;
    }

    setIsConnecting(true);
    setError(null);

    try {
      const eth = (window as any).ethereum;
      const accounts = await eth.request({
        method: "eth_requestAccounts",
      });

      if (!accounts || accounts.length === 0) {
        throw new Error("No accounts authorized by user.");
      }

      const connectedAddress = accounts[0];
      setAddress(connectedAddress);

      // Attempt to switch to Base network (8453 / 0x2105)
      try {
        await eth.request({
          method: "wallet_switchEthereumChain",
          params: [{ chainId: BASE_CHAIN_ID }],
        });
        setChainId(BASE_CHAIN_ID);
      } catch (switchError: any) {
        // Chain not added to wallet yet
        if (switchError.code === 4902) {
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
    } catch (err: any) {
      setError(err?.message || "User rejected connection request.");
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

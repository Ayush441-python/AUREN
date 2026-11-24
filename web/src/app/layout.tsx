import type { Metadata } from "next";
import { Cormorant_Garamond, Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geist = Geist({
  variable: "--font-geist",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

const cormorant = Cormorant_Garamond({
  variable: "--font-cormorant",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "AUREN — Portfolio Risk Intelligence",
    template: "%s — AUREN",
  },
  description:
    "Institutional-grade portfolio risk analytics for liquid equities, ETFs, and crypto. Deterministic, mathematically verified, transparent.",
  icons: {
    icon: "/favicon.ico",
  },
  openGraph: {
    title: "AUREN — Risk has layers. See them all.",
    description:
      "A cinematic risk intelligence platform for understanding exposure, correlation, and portfolio vulnerability.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${geist.variable} ${geistMono.variable} ${cormorant.variable}`}
    >
      <body className="min-h-screen bg-obsidian text-primary antialiased selection:bg-gold/20 selection:text-highlight">
        {children}
      </body>
    </html>
  );
}

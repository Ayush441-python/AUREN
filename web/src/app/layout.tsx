import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AUREN — Portfolio Risk Intelligence",
  description:
    "Institutional-grade portfolio risk analytics for liquid equities, ETFs, and crypto. Deterministic, mathematically verified, transparent.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full dark antialiased">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col bg-[#0E0E10] text-[#F5F6F7] selection:bg-[#E3B341]/20 selection:text-[#F5F6F7]">
        {children}
      </body>
    </html>
  );
}

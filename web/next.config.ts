import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async redirects() {
    return [
      {
        source: "/proof",
        destination: "/dashboard?tab=docs",
        permanent: false,
      },
      {
        source: "/api-docs",
        destination: "/dashboard?tab=docs",
        permanent: false,
      },
      {
        source: "/new",
        destination: "/dashboard?new=1",
        permanent: false,
      },
      {
        source: "/p/:id",
        destination: "/dashboard?portfolio=:id",
        permanent: false,
      },
      {
        source: "/workstation",
        destination: "/dashboard",
        permanent: false,
      },
    ];
  },
};

export default nextConfig;

import type { NextConfig } from "next";
import bundleAnalyzer from "@next/bundle-analyzer";

const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === "true",
});

const localPort = process.env.GEOAI_LOCAL_API_PORT ?? "8001";
if (!/^\d{1,5}$/.test(localPort) || Number(localPort) < 1024 || Number(localPort) > 65535) {
  throw new Error("GEOAI_LOCAL_API_PORT must be a local unprivileged TCP port");
}

const nextConfig: NextConfig = {
  distDir: process.env.GEOAI_BETA_VALIDATION === "true" ? ".next-beta" : process.env.GEOAI_LOCAL_REVIEW === "true" ? ".next-phase1" : ".next",
  poweredByHeader: false,
  env: process.env.GEOAI_LOCAL_REVIEW === "true" ? {NEXT_PUBLIC_API_URL:"/local-api"} : {},
  // Local review keeps browser traffic on one origin. Backend authentication and
  // authorization still run unchanged; no user-supplied proxy destination.
  async rewrites() {
    const apiPort = process.env.GEOAI_LOCAL_API_PORT ?? "8001";
    return process.env.GEOAI_LOCAL_REVIEW === "true"
      ? [{ source: "/local-api/:path*", destination: `http://127.0.0.1:${apiPort}/:path*` }]
      : [];
  },
  compress: true,
  images: {
    formats: ["image/avif", "image/webp"],
    minimumCacheTTL: 60 * 60 * 24 * 30,
  },
  experimental: {
    // Keep local development disk use bounded; hot reload still uses memory.
    // Cold restarts recompile instead of retaining gigabytes of compiler cache.
    turbopackFileSystemCacheForDev: false,
    optimizePackageImports: ["lucide-react", "framer-motion", "recharts"],
  },
};

export default withBundleAnalyzer(nextConfig);

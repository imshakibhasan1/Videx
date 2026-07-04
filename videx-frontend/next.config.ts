import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // ── Rewrites: Proxy /api/v1/* to FastAPI backend (avoids CORS in dev) ──
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/:path*`,
      },
    ];
  },

  // ── Image domains (for Cloudinary thumbnails) ──
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "res.cloudinary.com",
      },
    ],
  },

  // ── TypeScript strict mode ──
  typescript: {
    ignoreBuildErrors: false,
  },

  // ── Experimental features ──
  experimental: {
    optimizePackageImports: ["lucide-react", "framer-motion"],
  },
};

export default nextConfig;

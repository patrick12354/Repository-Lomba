import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  serverExternalPackages: ["better-sqlite3", "nodemailer"],
  // The SQLite file is read at runtime, so it has to travel with every serverless function.
  outputFileTracingIncludes: {
    "/**/*": ["./data/partpulse.db"],
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;

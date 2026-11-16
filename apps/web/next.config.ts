import path from "node:path";

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: ["three"],
  // Monorepo root (where package-lock.json is). Without this, if there is another package-lock.json in a
  // parent folder (for example in the Windows home), Next takes it as the root and resolves the
  // modules wrongly.
  outputFileTracingRoot: path.join(__dirname, "../.."),
};

export default nextConfig;

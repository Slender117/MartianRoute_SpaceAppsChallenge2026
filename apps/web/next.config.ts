import path from "node:path";

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: ["three"],
  // Raíz del monorepo (donde está package-lock.json). Sin esto, si hay otro package-lock.json en una
  // carpeta superior (por ejemplo en el home de Windows), Next la toma como raíz y resuelve mal los
  // módulos.
  outputFileTracingRoot: path.join(__dirname, "../.."),
};

export default nextConfig;

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["framer-motion"],
  allowedDevOrigins: ["192.168.1.69"],
};

export default nextConfig;

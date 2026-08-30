import path from "node:path";
import { networkInterfaces } from "node:os";
import type { NextConfig } from "next";

const localNetworkOrigins = Object.values(networkInterfaces())
  .flat()
  .filter((address) => address?.family === "IPv4" && !address.internal)
  .map((address) => address!.address);

const nextConfig: NextConfig = {
  output: "standalone",
  // Keep phone testing working even when DHCP changes the computer's LAN address.
  allowedDevOrigins: ["127.0.0.1", "localhost", ...localNetworkOrigins],
  turbopack: {
    root: path.resolve(__dirname),
  },
};

export default nextConfig;

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "example.com",
      },
      // 필요 시 나중에 S3, 카카오 프로필 등 추가
    ],
  },
};

export default nextConfig;

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    // [추가] 외부 이미지 호스트 허용 설정
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'example.com',
        port: '',
        pathname: '/**',
      },
      {
        protocol: "https",
        hostname: "s3.cloud",
        port: "",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "dqee7nuafmp2e.cloudfront.net",
        port: "",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "example.com",
        port: "",
        pathname: "/**",
      },
    ],
  },
};

export default nextConfig;

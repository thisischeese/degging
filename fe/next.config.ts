import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  images: {
    // [추가] 외부 이미지 호스트 허용 설정
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 's3.cloud', // 에러가 났던 목업 이미지 도메인
        port: '',
        pathname: '/**', // 해당 도메인의 모든 경로 허용
      },
      // Tip: 나중에 실제 S3 버킷 주소가 나오면 여기에 같은 방식으로 추가하세요
      // {
      //   protocol: 'https',
      //   hostname: '본인의-s3-버킷명.s3.ap-northeast-2.amazonaws.com',
      //   port: '',
      //   pathname: '/**',
      // },
      ],
  },

  // (선택 사항) Turbopack 관련 설정이나 리다이렉트가 필요하면 여기에 추가합니다.
};

export default nextConfig;

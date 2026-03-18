"use client";

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

/** 
 * 데이터의 성격에 따른 React Query 옵션 설정
 * useQuery 등에서 { ...QUERY_OPTIONS.STATIC } 처럼 가져다 쓸 수 있습니다.
 */
export const QUERY_OPTIONS = {
  // 1. 거의 변하지 않는 데이터 (예: 카테고리 목록, 태그 목록)
  STATIC: {
    staleTime: 10 * 60 * 1000, // 10분
    gcTime: 15 * 60 * 1000,    // 15분
  },
  // 2. 일반적인 데이터 (예: 카페 목록, 추천 검색어)
  GENERAL: {
    staleTime: 60 * 1000,      // 1분
    gcTime: 5 * 60 * 1000,     // 5분
  },
  // 3. 민감하거나 실시간이 중요한 데이터 (예: 내 프로필, 알림, 장바구니)
  SENSITIVE: {
    staleTime: 0,             // 즉시 만료 (항상 서버 확인)
    gcTime: 1 * 60 * 1000,     // 1분
  },
} as const;

export default function QueryProvider({ children }: { children: React.ReactNode }) {
  const [query_client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            ...QUERY_OPTIONS.GENERAL, // 기본은 '일반 데이터' 설정을 따름
            refetchOnWindowFocus: false, // 창 활성화 시 자동 새로고침 끄기
            retry: 1, // API 실패 시 1번 더 재시도
          },
        },
      })
  );
  return (
    <QueryClientProvider client={query_client}>
      {children}
    </QueryClientProvider>
  );
}
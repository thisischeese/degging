"use client";

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

export default function QueryProvider({ children }: { children: React.ReactNode }) {
  const [query_client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 기본 1분 (일반 콘텐츠 기준)
            gcTime: 5 * 60 * 1000, // 기본 5분
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
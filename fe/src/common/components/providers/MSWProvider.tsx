'use client';

import { useEffect, useState } from 'react';

export const MSWProvider = ({ children }: { children: React.ReactNode }) => {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const initMSW = async () => {
      // 개발 환경에서만 MSW 활성화
      if (process.env.NODE_ENV === 'development') {
        if (typeof window !== 'undefined') {
          const { worker } = await import('@/mocks/browser');
          await worker.start({
            onUnhandledRequest: 'bypass', // 정의되지 않은 요청은 무시하고 통과시킴
          });
        }
      }
      setIsReady(true);
    };

    initMSW();
  }, []);

  if (!isReady) {
    // MSW가 준비되기 전에는 자식 컴포넌트를 렌더링하지 않음 (선택 사항)
    // return null; 또는 로딩 스피너
    return null;
  }

  return <>{children}</>;
};

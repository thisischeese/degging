"use client";

import { useEffect, useRef } from "react";
import Image from "next/image";

interface StepLoadingProps {
  next: () => void;
  // 실제 가입 로직을 여기서 실행하기 위해 props 추가 제안
  onSignup?: () => Promise<void>;
}

export default function StepLoading({ next, onSignup }: StepLoadingProps) {
  
  const hasRequested = useRef(false);

  useEffect(() => {
    let timeoutId: NodeJS.Timeout;

    const runSignup = async () => {
      if (hasRequested.current) return;
      hasRequested.current = true;

      try {
        // 1. 서버 통신 시작 (onSignup 실행)
        if (onSignup) {
          await onSignup();
        }
        
        // 2. 통신이 성공하면 3초간 "분석 중" 화면을 보여준 뒤 다음 단계로
        timeoutId = setTimeout(() => {
          next();
        }, 3000);
      } catch (error) {
        console.error("가입 중 에러 발생:", error);
        // 에러 시 로직 (예: 이전 단계로 돌보내기 등)을 여기에 추가할 수 있습니다.
        hasRequested.current = false; // 에러 시 다시 시도할 수 있도록 초기화
      }
    };

    runSignup();

    return () => {
      clearTimeout(timeoutId); // 언마운트 시 타이머 정리
    };
  }, [next, onSignup]);

  return (
    <div className="flex flex-col h-full items-center justify-between py-20">
      {/* 상단 타이틀 */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 font-pretendard">
          취향 분석 중...
        </h2>
      </div>

      {/* 중앙 겹쳐진 이미지 영역 (피그마 재현) */}
      <div className="relative w-full max-w-[280px] aspect-square">
        {/* 첫 번째 이미지 (왼쪽 위, 살짝 회전) */}
        <div className="absolute top-0 left-0 w-40 h-40 rounded-3xl overflow-hidden shadow-xl -rotate-12 z-10 border-2 border-white">
          <Image src="/images/auth/taste1.webp" alt="taste1" fill className="object-cover" />
        </div>

        {/* 두 번째 이미지 (오른쪽 위, 반대 방향 회전) */}
        <div className="absolute top-4 right-0 w-44 h-44 rounded-3xl overflow-hidden shadow-xl rotate-6 z-20 border-2 border-white">
          <Image src="/images/auth/taste2.webp" alt="taste2" fill className="object-cover" />
        </div>

        {/* 세 번째 이미지 (중앙 아래, 크게 배치) */}
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-52 h-64 rounded-3xl overflow-hidden shadow-2xl z-30 border-2 border-white">
          <Image src="/images/auth/taste3.webp" alt="taste3" fill className="object-cover" />
        </div>
      </div>

      {/* 하단 로고 */}
      <div className="flex flex-col items-center">
        <Image src="/images/common/logo.png" alt="Logo" width={60} height={60} className="object-contain opacity-50" />
      </div>
    </div>
  );
}
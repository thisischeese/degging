"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Button from "@/common/components/Button";
import { SignupStepProps } from "../types";
import { useQuery } from "@tanstack/react-query";
import { getOnboardingCafes } from "@/features/onboarding/api/onboardingApi";
import { QUERY_OPTIONS } from "@/common/components/providers/QueryProvider";
import { getImageUrl } from "@/common/utils/image";
import { OnboardingCafe } from "@/features/onboarding/types";

export default function StepMood({ next, formData }: SignupStepProps) {
  const { data: cafeData } = useQuery({
    queryKey: ["cafes", "onboarding"],
    queryFn: getOnboardingCafes,
    ...QUERY_OPTIONS.STATIC,
  });

  const cafes = cafeData || [];
  const [selectedMoods, setSelectedMoods] = useState<string[]>(formData.moods || []);
  const [errorMessage, setErrorMessage] = useState("");

  // StepLoading에서 사용할 이미지들을 미리 로드해둡니다.
  useEffect(() => {
    const imagesToPreload = [ 
      "/images/auth/taste1.webp",
      "/images/auth/taste2.webp",
      "/images/auth/taste3.webp",
    ];
    imagesToPreload.forEach((src) => {
      if (typeof window !== "undefined") {
        const img = new window.Image();
        img.src = src;
      }
    });
  }, []);

  const toggleMood = (cafeId: string) => {
    setErrorMessage("");
    if (selectedMoods.includes(cafeId)) {
      setSelectedMoods((prev) => prev.filter((id) => id !== cafeId));
    } else {
      if (selectedMoods.length >= 3) {
        setErrorMessage("최대 3개까지만 선택 가능합니다!");
        return;
      }
      setSelectedMoods((prev) => [...prev, cafeId]);
    }
  };

  const handleNext = () => {
    if (selectedMoods.length !== 3) {
      setErrorMessage("정확한 취향 파악을 위해 3개를 선택해주세요!");
      return;
    }
    next({ moods: selectedMoods });
  };

  return (
    // main의 px-6 py-8을 -mx-6 -mt-8으로 상쇄하여 full-width / 상단 여백 제거
    <div className="flex flex-col flex-1 min-h-0 -mx-6 -mt-8">

      {/* 1. 타이틀 영역 */}
      <div className="pt-6 px-6 shrink-0 text-center">
        <h2 className="text-[22px] font-bold text-gray-900 tracking-tight font-pretendard">
          내 취향 카페 분위기는?
        </h2>
        <p className="text-[13px] text-gray-500 mt-1 font-pretendard">
          사용자 취향에 딱 맞는 카페를 보여드립니다
        </p>
      </div>

      {/* 2. 이미지 그리드: 고정 영역을 제외하고 스크롤 가능 */}
      <div className="flex-1 min-h-0 mt-4 px-6 overflow-y-auto no-scrollbar">
        <div className="grid grid-cols-2 gap-3 pb-6">
          {cafes.map((cafe, index) => (
            <MoodItem
              key={cafe.cafeId}
              cafe={cafe}
              isActive={selectedMoods.includes(cafe.cafeId)}
              onToggle={() => toggleMood(cafe.cafeId)}
              isPriority={index < 4}
            />
          ))}
        </div>
      </div>

      {/* 3. 하단 버튼 영역: 상단에 얇은 선(경계) 추가하여 스크롤 영역과 분리 */}
      <div className="shrink-0 pb-4 mt-2 px-6 border-t border-gray-100 pt-4">
        <div className="min-h-[24px] mb-2 text-center">
          {errorMessage && (
            <p className="text-[14px] text-[#C3304F] font-bold leading-tight animate-bounce">
              {errorMessage}
            </p>
          )}
        </div>

        <Button
          variant={selectedMoods.length === 3 ? "primary" : "gray"}
          size="full"
          onClick={handleNext}
          className="shadow-lg active:scale-[0.98] transition-all"
        >
          다음 단계로
        </Button>
      </div>
    </div>
  );
}

// 개별 무드 아이템 컴포넌트 (스켈레톤 처리 포함)
function MoodItem({ 
  cafe, 
  isActive, 
  onToggle,
  isPriority
}: { 
  cafe: OnboardingCafe; 
  isActive: boolean; 
  onToggle: () => void;
  isPriority: boolean;
}) {
  const [isLoaded, setIsLoaded] = useState(false);

  // 이미지 경로 처리: raw UUID인 경우 'cafe/' 접두사 추가
  const rawPath = cafe.thumbnailUrl;
  const formattedPath = rawPath && !rawPath.startsWith("http") && !rawPath.includes("/")
    ? `cafe/${rawPath}`
    : rawPath;

  return (
    <div
      onClick={onToggle}
      className="relative cursor-pointer"
    >
      <div className={`relative aspect-square rounded-[16px] overflow-hidden border-[3px] transition-all duration-200 bg-gray-100 ${
        isActive ? "border-[#C3304F] shadow-[0_0_15px_rgba(195,48,79,0.3)]" : "border-transparent"
      }`}>
        {/* 스켈레톤 레이어 */}
        {!isLoaded && (
          <div className="absolute inset-0 bg-gray-200 animate-pulse z-10" />
        )}
        
        <Image
          src={getImageUrl(formattedPath)}
          alt="Cafe Mood"
          fill
          sizes="(max-width: 768px) 50vw, 33vw"
          priority={isPriority}
          onLoad={() => setIsLoaded(true)}
          className={`object-cover transition-transform duration-300 ${
            isActive ? "scale-105" : "scale-100"
          } ${isLoaded ? "opacity-100" : "opacity-0"}`}
        />
      </div>
    </div>
  );
}
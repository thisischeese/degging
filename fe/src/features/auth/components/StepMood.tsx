"use client";

import { useState } from "react";
import Image from "next/image";
import Button from "@/common/components/Button";
import { SignupStepProps } from "../types";

import { useQuery } from "@tanstack/react-query";
import { getOnboardingCafes } from "@/features/onboarding/api/onboardingApi";
import { QUERY_OPTIONS } from "@/common/components/providers/QueryProvider";

export default function StepMood({ next, updateData, formData }: SignupStepProps) {
  const { data: cafeData } = useQuery({
    queryKey: ["cafes", "onboarding"],
    queryFn: getOnboardingCafes,
    ...QUERY_OPTIONS.STATIC,
  });

  const cafes = cafeData || [];
  const [selectedMoods, setSelectedMoods] = useState<string[]>(formData.moods || []);
  const [errorMessage, setErrorMessage] = useState("");

  const toggleMood = (cafeId: string) => {
    setErrorMessage("");
    if (selectedMoods.includes(cafeId)) {
      setSelectedMoods((prev) => prev.filter((id) => id !== cafeId));
    } else {
      if (selectedMoods.length >= 3) {
        setErrorMessage("최대 3개까지만 선택할 수 있습니다.");
        return;
      }
      setSelectedMoods((prev) => [...prev, cafeId]);
    }
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
          {cafes.map((cafe) => {
            const isActive = selectedMoods.includes(cafe.cafeId);
            return (
              <div
                key={cafe.cafeId}
                onClick={() => toggleMood(cafe.cafeId)}
                className="relative cursor-pointer"
              >
                <div className={`relative aspect-square rounded-[16px] overflow-hidden border-[3px] transition-all duration-200 ${
                  isActive ? "border-[#C3304F] shadow-[0_0_15px_rgba(195,48,79,0.3)]" : "border-transparent"
                }`}>
                  <Image
                    src={cafe.thumbnailUrl}
                    alt="Cafe Mood"
                    fill
                    className={`object-cover transition-transform duration-300 ${isActive ? "scale-105" : "scale-100"}`}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. 하단 버튼 영역: 상단에 얇은 선(경계) 추가하여 스크롤 영역과 분리 */}
      <div className="shrink-0 pb-4 mt-2 px-6 border-t border-gray-100 pt-4">
        <div className="min-h-[24px] mb-2 text-center">
          {(errorMessage || selectedMoods.length === 0) && (
            <p className="text-[12px] text-[#C3304F] font-medium leading-tight">
              {errorMessage || "취향을 정확히 파악하기 위해 하나 이상 선택해주세요!"}
            </p>
          )}
        </div>

        <Button
          variant="gray"
          size="full"
          disabled={selectedMoods.length === 0}
          onClick={() => {
            updateData({ moods: selectedMoods });
            next();
          }}
          className={selectedMoods.length > 0 ? "bg-[#C3304F]! text-white!" : ""}
        >
          다음 단계로
        </Button>
      </div>
    </div>
  );
}
"use client";

import { useState } from "react";
import Image from "next/image";
import Button from "@/common/components/Button";
import { SignupStepProps } from "../types";
import cafeImg from "@/assets/images/cafe/cafe1.png";

const MOOD_LIST = [
  { id: "mood1", label: "조용한", image: cafeImg },
  { id: "mood2", label: "힙한", image: cafeImg },
  { id: "mood3", label: "대화하기 좋은", image: cafeImg },
  { id: "mood4", label: "작업하기 좋은", image: cafeImg },
  { id: "mood5", label: "사진이 잘 나오는", image: cafeImg },
  { id: "mood6", label: "디저트가 맛있는", image: cafeImg },
  { id: "mood7", label: "반려동물 동반", image: cafeImg },
  { id: "mood8", label: "뷰가 좋은", image: cafeImg },
];

export default function StepMood({ next, updateData, formData }: SignupStepProps) {
  const [selectedMoods, setSelectedMoods] = useState<string[]>(formData.moods || []);
  const [errorMessage, setErrorMessage] = useState("");

  const toggleMood = (moodId: string) => {
    setErrorMessage("");
    if (selectedMoods.includes(moodId)) {
      setSelectedMoods((prev) => prev.filter((id) => id !== moodId));
    } else {
      if (selectedMoods.length >= 3) {
        setErrorMessage("최대 3개까지만 선택할 수 있습니다.");
        return;
      }
      setSelectedMoods((prev) => [...prev, moodId]);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      
      {/* 1. 타이틀 영역: 양옆 패딩 유지 및 고정 */}
      <div className="mt-14 px-6 shrink-0 text-center">
        <h2 className="text-[26px] font-bold text-gray-900 tracking-tight font-pretendard">
          내 취향 카페 분위기는?
        </h2>
        <p className="text-[14px] text-gray-500 mt-2 font-pretendard">
          사용자 취향에 딱 맞는 카페를 보여드립니다
        </p>
      </div>

      {/* 2. 이미지 리스트 영역: 내부 스크롤 완벽 구현 */}
      <div className="flex-1 min-h-0 mt-8 px-6 overflow-y-auto no-scrollbar">
        <div className="grid grid-cols-2 gap-4 pb-8">
          {MOOD_LIST.map((mood) => {
            const isActive = selectedMoods.includes(mood.id);
            return (
              <div
                key={mood.id}
                onClick={() => toggleMood(mood.id)}
                className="relative cursor-pointer group"
              >
                {/* 피그마 기준 정사각형 비율 aspect-square 적용 */}
                <div className={`relative aspect-square rounded-[24px] overflow-hidden border-[3px] transition-all duration-200 ${
                  isActive ? "border-[#C3304F]" : "border-transparent"
                }`}>
                  <Image
                    src={mood.image}
                    alt={mood.label}
                    fill
                    className={`object-cover transition-transform duration-300 ${isActive ? "scale-105" : "scale-100"}`}
                  />
                  {/* 텍스트 가독성을 위한 그라데이션 오버레이 */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent flex items-end p-4">
                    <span className="text-white font-bold text-[15px] leading-tight">
                      #{mood.label}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. 하단 버튼 영역: 배경색을 제거하여 컨테이너 느낌 삭제 */}
      <div className="shrink-0 px-6 pb-10">
        <div className="min-h-[24px] mb-4 text-center">
          {(errorMessage || selectedMoods.length === 0) && (
            <p className="text-[13px] text-[#C3304F] font-medium leading-tight">
              {errorMessage || "사용자의 취향을 정확히 파악하기 위해 하나 이상 선택해주세요!"}
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
          className={`h-[54px] !rounded-xl transition-all ${
            selectedMoods.length > 0 ? "!bg-[#C3304F] !text-white shadow-md" : ""
          }`}
        >
          선택 완료
        </Button>
      </div>
    </div>
  );
}
"use client";

import { useState } from "react";
import Image from "next/image";
import Button from "@/common/components/Button";
import { SignupStepProps } from "../types";

const MOOD_LIST = [
  { id: "mood1", label: "조용한", image: "/images/cafe/cafe1.png" },
  { id: "mood2", label: "힙한", image: "/images/cafe/cafe1.png" },
  { id: "mood3", label: "대화하기 좋은", image: "/images/cafe/cafe1.png" },
  { id: "mood4", label: "작업하기 좋은", image: "/images/cafe/cafe1.png" },
  { id: "mood5", label: "사진이 잘 나오는", image: "/images/cafe/cafe1.png" },
  { id: "mood6", label: "디저트가 맛있는", image: "/images/cafe/cafe1.png" },
  { id: "mood7", label: "반려동물 동반", image: "/images/cafe/cafe1.png" },
  { id: "mood8", label: "뷰가 좋은", image: "/images/cafe/cafe1.png" },
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

      {/* 2. 이미지 그리드: 스크롤 없이 한 화면에 꽉 차도록 */}
      <div className="flex-1 min-h-0 mt-4 px-4 overflow-y-auto no-scrollbar">
        <div className="grid grid-cols-2 gap-2.5 pb-2">
          {MOOD_LIST.map((mood) => {
            const isActive = selectedMoods.includes(mood.id);
            return (
              <div
                key={mood.id}
                onClick={() => toggleMood(mood.id)}
                className="relative cursor-pointer"
              >
                {/* aspect-[5/3]으로 세로를 줄여서 8개가 한 화면에 들어오게 */}
                <div className={`relative aspect-[5/3] rounded-[16px] overflow-hidden border-[3px] transition-all duration-200 ${
                  isActive ? "border-[#C3304F]" : "border-transparent"
                }`}>
                  <Image
                    src={mood.image}
                    alt={mood.label}
                    fill
                    className={`object-cover transition-transform duration-300 ${isActive ? "scale-105" : "scale-100"}`}
                  />
                  {/* 텍스트 가독성을 위한 그라데이션 오버레이 */}
                  <div className="absolute inset-0 bg-linear-to-t from-black/50 via-transparent to-transparent flex items-end p-3">
                    <span className="text-white font-bold text-[13px] leading-tight">
                      #{mood.label}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. 하단 버튼 영역 */}
      <div className="shrink-0 px-6 pb-8">
        <div className="min-h-[20px] mb-3 text-center">
          {(errorMessage || selectedMoods.length === 0) && (
            <p className="text-[12px] text-[#C3304F] font-medium leading-tight">
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
          className={`h-[54px] rounded-xl! transition-all ${
            selectedMoods.length > 0 ? "bg-[#C3304F]! text-white! shadow-md" : ""
          }`}
        >
          선택 완료
        </Button>
      </div>
    </div>
  );
}
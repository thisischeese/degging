"use client";

import { useState } from "react";
import { Chip } from "@/common/components/Chip";
import Button from "@/common/components/Button";
import { SignupStepProps } from "../types";
import { useQuery } from "@tanstack/react-query";
import { getOnboardingRankings } from "@/features/ranks/api/rankingApi";
import { QUERY_OPTIONS } from "@/common/components/providers/QueryProvider";

// 기존 DUMMY_MENUS를 제거하고 API 데이터를 사용합니다.

export default function StepTrend({ next, updateData, formData }: SignupStepProps) {
  // 온보딩 랭킹 데이터 조회 (정적 데이터 성격이 강하므로 STATIC 옵션 적용)
  const { data: rankingData } = useQuery({
    queryKey: ["rankings", "onboarding"],
    queryFn: getOnboardingRankings,
    ...QUERY_OPTIONS.STATIC,
  });
  
  // 랭킹 키워드만 추출하여 메뉴 리스트 생성
  const menus = rankingData?.data.rankings.map(item => item.keyword) || [];

  const [selectedMenus, setSelectedMenus] = useState<string[]>(formData.trends || []);
  const [errorMessage, setErrorMessage] = useState("");

  const toggleMenu = (menu: string, index: number) => {
    const uniqueKey = `${menu}-${index}`;
    setErrorMessage("");
    if (selectedMenus.includes(uniqueKey)) {
      setSelectedMenus((prev) => prev.filter((item) => item !== uniqueKey));
    } else {
      if (selectedMenus.length >= 5) {
        setErrorMessage("최대 5개까지 선택 가능합니다!");
        return;
      }
      setSelectedMenus((prev) => [...prev, uniqueKey]);
    }
  };

  return (
    <div className="flex flex-col h-full px-4 overflow-hidden">
      {/* 1. 타이틀 영역 */}
      <div className="mt-14 shrink-0 text-center">
        <h2 className="text-[26px] font-bold text-gray-900 tracking-tight font-pretendard">
          나의 애착 메뉴는?
        </h2>
        <p className="text-[14px] text-gray-500 mt-2 font-pretendard">
          사용자의 취향에 딱 맞는 디저트를 보여드립니다
        </p>
      </div>

      {/* 2. 중앙 칩 영역: 레이아웃 고정 */}
      <div className="flex-1 flex items-center justify-center min-h-0 py-6">
        <div className="max-h-full overflow-y-auto no-scrollbar">
          <div className="flex flex-wrap gap-x-2 gap-y-4 justify-center max-w-[360px] mx-auto pb-4">
            {menus.map((menu, index) => {
              const uniqueKey = `${menu}-${index}`;
              const isActive = selectedMenus.includes(uniqueKey);
              return (
                <div key={uniqueKey} className="relative">
                  <Chip
                    label={menu}
                    variant="onboarding"
                    isActive={isActive}
                    onClick={() => toggleMenu(menu, index)}
                    /* [&_svg]:hidden: 칩 내부의 체크 아이콘(SVG)을 강제로 숨김
                      scale 제거: 레이아웃이 변하지 않도록 설정
                    */
                    className={`
                      w-auto px-5 py-2.5 text-[14px] transition-colors duration-200
                      [&_svg]:hidden [&_img]:hidden
                      ${isActive 
                        ? "font-bold border-[#C3304F] bg-[#F9EBEF] text-[#C3304F]" 
                        : "border-gray-200 bg-white text-gray-600"}
                    `}
                  />
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 3. 에러 메시지 및 하단 버튼 영역 */}
      <div className="shrink-0 pb-10">
        <div className="min-h-[24px] mb-4 text-center">
          {(errorMessage || selectedMenus.length === 0) && (
            <p className="text-[13px] text-[#C3304F] font-medium leading-tight">
              {errorMessage || "사용자의 취향을 정확히 파악하기 위해 하나 이상 선택해주세요!"}
            </p>
          )}
        </div>

        <Button
          variant="gray"
          size="full"
          disabled={selectedMenus.length === 0}
          onClick={() => {
            updateData({ trends: selectedMenus });
            next();
          }}
          // 버튼 위치가 고정되도록 상단 여백이나 크기 변화 요소를 최소화함
          className={`h-[54px] rounded-xl! transition-all ${
            selectedMenus.length > 0 ? "bg-[#C3304F]! text-white! shadow-md" : ""
          }`}
        >
          다음 단계로
        </Button>
      </div>
    </div>
  );
}
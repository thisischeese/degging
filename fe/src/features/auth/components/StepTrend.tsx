"use client";

import { useState } from "react";
import Image from "next/image";
import { Chip } from "@/common/components/Chip";

import Button from "@/common/components/Button";
import { SignupStepProps } from "../types";
import { useQuery } from "@tanstack/react-query";
import { getOnboardingMenus, getOnboardingCafes } from "@/features/onboarding/api/onboardingApi";
import { QUERY_OPTIONS } from "@/common/components/providers/QueryProvider";
import { getImageUrl } from "@/common/utils/image";

export default function StepTrend({ next, formData }: SignupStepProps) {
  // 온보딩 랭킹 데이터 조회 (정적 데이터 성격이 강하므로 STATIC 옵션 적용)
  const { data: rankingData } = useQuery({
    queryKey: ["rankings", "onboarding"],
    queryFn: getOnboardingMenus,
    ...QUERY_OPTIONS.STATIC,
  });

  // [프리페칭] 다음 단계인 StepMood에서 사용할 카페 데이터를 미리 불러와 캐시에 저장합니다.
  const { data: cafeData } = useQuery({
    queryKey: ["cafes", "onboarding"],
    queryFn: getOnboardingCafes,
    ...QUERY_OPTIONS.STATIC,
  });
  
  const menus = rankingData || [];
  const [selectedMenus, setSelectedMenus] = useState<string[]>([]);
  const [errorMessage, setErrorMessage] = useState("");

  const toggleMenu = (keyword: string) => {
    setErrorMessage("");
    if (selectedMenus.includes(keyword)) {
      setSelectedMenus((prev) => prev.filter((k) => k !== keyword));
    } else {
      if (selectedMenus.length >= 3) {
        setErrorMessage("최대 3개까지만 선택 가능합니다.");
        return;
      }
      setSelectedMenus((prev) => [...prev, keyword]);
    }
  };

  const handleNext = () => {
    if (selectedMenus.length !== 3) {
      setErrorMessage("정확히 3개의 메뉴를 선택해주세요!");
      return;
    }
    // keyword로 선택 후, menuId(number)로 변환하여 API 명세에 맞게 전송
    const selectedMenuIds = menus
      .filter((m) => selectedMenus.includes(m.keyword))
      .map((m) => String(m.menuId));
    next({ trends: selectedMenuIds });
  };

  return (
    <div className="flex flex-col h-full px-4 overflow-hidden relative">
      {/* 1. 타이틀 영역 */}
      <div className="mt-14 shrink-0 text-center">
        <h2 className="text-[26px] font-bold text-gray-900 tracking-tight font-pretendard">
          나의 애착 메뉴는?
        </h2>
        <p className="text-[14px] text-gray-500 mt-2 font-pretendard">
          사용자의 취향에 딱 맞는 디저트를 보여드립니다
        </p>
      </div>

      {/* 2. 중앙 칩 영역: 기존 디자인 복원 */}
      <div className="flex-1 flex items-center justify-center min-h-0 py-6">
        <div className="max-h-full overflow-y-auto no-scrollbar">
          <div className="flex flex-wrap gap-x-2 gap-y-4 justify-center max-w-[360px] mx-auto pb-4">
            {menus.map((menu, index) => {
              const isActive = selectedMenus.includes(menu.keyword);
              return (
                <div key={`${menu.keyword}-${index}`} className="relative">
                  <Chip
                    label={menu.keyword}
                    variant="onboarding"
                    isActive={isActive}
                    onClick={() => toggleMenu(menu.keyword)}
                    className="w-auto px-5 py-2.5 text-[14px] transition-colors duration-200 [&_svg]:hidden"
                  />
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 3. 에러 메시지 및 하단 버튼 영역 */}
      <div className="pb-4 mt-2">
        <div className="min-h-[24px] mb-2 text-center">
          {errorMessage && (
            <p className="text-[14px] text-[#C3304F] font-bold leading-tight animate-bounce">
              {errorMessage}
            </p>
          )}
        </div>

        <Button
          variant={selectedMenus.length === 3 ? "primary" : "gray"}
          size="full"
          onClick={handleNext}
          className="shadow-lg active:scale-[0.98] transition-all"
        >
          다음 단계로
        </Button>
      </div>

      {/* [브라우저 프리로딩] 다음 단계(StepMood) 이미지들을 미리 로드 (Next.js 캐시 적중용) */}
      <div className="absolute opacity-0 pointer-events-none w-0 h-0 overflow-hidden" aria-hidden="true">
        {cafeData?.slice(0, 6).map((cafe) => {
           const rawPath = cafe.thumbnailUrl;
           const formattedPath = rawPath && !rawPath.startsWith("http") && !rawPath.includes("/")
             ? `cafe/${rawPath}`
             : rawPath;
           return (
             <div key={`preload-${cafe.cafeId}`} className="relative h-px w-px">
               <Image 
                 src={getImageUrl(formattedPath)} 
                 alt="preload"
                 fill
                 sizes="(max-width: 768px) 50vw, 33vw" // StepMood와 일치
                 priority={true} 
               />
             </div>
           );
        })}
      </div>
    </div>
  );
}
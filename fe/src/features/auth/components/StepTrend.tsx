"use client";

import { useState } from "react";
import Image from "next/image";
import Button from "@/common/components/Button";
import { SignupStepProps } from "../types";
import { useQuery } from "@tanstack/react-query";
import { getOnboardingMenus, getOnboardingCafes } from "@/features/onboarding/api/onboardingApi";
import { QUERY_OPTIONS } from "@/common/components/providers/QueryProvider";
import { getImageUrl } from "@/common/utils/image";

// 기존 DUMMY_MENUS를 제거하고 API 데이터를 사용합니다.

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
  
  // 랭킹 키워드만 추출하여 메뉴 리스트 생성 (언래핑된 데이터를 바로 사용)
  const menus = rankingData || [];
  const [selectedMenus, setSelectedMenus] = useState<number[]>(
    formData.trends.map((id) => Number(id))
  );
  const [errorMessage, setErrorMessage] = useState("");

  const toggleMenu = (menuId: number) => {
    setErrorMessage("");
    if (selectedMenus.includes(menuId)) {
      setSelectedMenus(selectedMenus.filter((id) => id !== menuId));
    } else {
      if (selectedMenus.length >= 3) {
        setErrorMessage("최대 3개까지만 선택 가능합니다.");
        return;
      }
      setSelectedMenus([...selectedMenus, menuId]);
    }
  };

  const handleNext = () => {
    if (selectedMenus.length !== 3) {
      setErrorMessage("정확히 3개의 메뉴를 선택해주세요!");
      return;
    }
    // SignupPage의 trends 상태는 일관성을 위해 string[]로 관리되고 있으므로 변환하여 넘김
    next({ trends: selectedMenus.map(String) });
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

      {/* 2. 중앙 메뉴 선택 영역 */}
      <div className="flex-1 overflow-y-auto no-scrollbar py-6">
        <div className="grid grid-cols-2 gap-4 max-w-[360px] mx-auto pb-4">
          {menus.map((menu) => (
            <div
              key={menu.menuId}
              onClick={() => toggleMenu(menu.menuId)}
              className={`flex flex-col items-center justify-center p-4 rounded-2xl border-2 transition-all cursor-pointer h-[100px] ${
                selectedMenus.includes(menu.menuId)
                  ? "border-[#C3304F] bg-[#F9EBEF] text-[#C3304F]"
                  : "border-gray-100 bg-white text-gray-500 hover:border-gray-200"
              }`}
            >
              <span className={`text-[16px] font-bold text-center leading-tight break-keep ${
                selectedMenus.includes(menu.menuId) ? "text-[#C3304F]" : "text-gray-800"
              }`}>
                {menu.keyword}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* 3. 에러 메시지 및 하단 버튼 영역 */}
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
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
  
  // 랭킹 데이터 (이제 문자열 배열)
  const menus = (rankingData as string[]) || [];

  const [selectedMenuNames, setSelectedMenuNames] = useState<string[]>(formData.trends || []);
  const [errorMessage, setErrorMessage] = useState("");

  const toggleMenu = (menuName: string) => {
    setErrorMessage("");
    if (selectedMenuNames.includes(menuName)) {
      setSelectedMenuNames((prev) => prev.filter((name) => name !== menuName));
    } else {
      if (selectedMenuNames.length >= 3) {
        setErrorMessage("최대 3개까지만 선택 가능합니다.");
        return;
      }
      setSelectedMenuNames((prev) => [...prev, menuName]);
    }
  };

  return (
    <div className="flex flex-col flex-1 min-h-0 -mx-6 -mt-8">
      {/* 1. 타이틀 영역 */}
      <div className="pt-6 px-6 shrink-0 text-center">
        <h2 className="text-[22px] font-bold text-gray-900 tracking-tight font-pretendard">
          요즘 내 스타일 디저트는?
        </h2>
        <p className="text-[13px] text-gray-500 mt-1 font-pretendard">
          가장 끌리는 디저트를 선택해주세요
        </p>
      </div>

      {/* 2. 중앙 칩 영역: 레이아웃 고정 */}
      <div className="flex-1 flex items-center justify-center min-h-0 py-6">
        <div className="max-h-full overflow-y-auto no-scrollbar">
          <div className="flex flex-wrap gap-x-2 gap-y-4 justify-center max-w-[360px] mx-auto pb-4">
            {menus.map((menuName, index) => {
              const isActive = selectedMenuNames.includes(menuName);
              return (
                <div key={`${menuName}-${index}`} className="relative">
                  <Chip
                    label={menuName}
                    variant="onboarding"
                    isActive={isActive}
                    onClick={() => toggleMenu(menuName)}
                    className="w-auto px-5 py-2.5 text-[14px] transition-colors duration-200 [&_svg]:hidden [&_img]:hidden"
                  />
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 3. 에러 메시지 및 하단 버튼 영역 */}
      <div className="pb-4 mt-2 px-6 border-t border-gray-100 pt-4">
        <div className="min-h-[24px] mb-2 text-center">
          {(errorMessage || selectedMenuNames.length !== 3) && (
            <p className="text-[14px] text-[#C3304F] font-bold leading-tight animate-bounce">
              {errorMessage || "취향 파악을 위해 3개를 정확히 선택해주세요!"}
            </p>
          )}
        </div>

        <Button
          variant={selectedMenuNames.length === 3 ? "primary" : "gray"}
          size="full"
          disabled={selectedMenuNames.length !== 3}
          onClick={() => {
            next({ trends: selectedMenuNames });
          }}
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
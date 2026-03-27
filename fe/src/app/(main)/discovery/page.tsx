"use client";

import { useEffect, useRef } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { pushGtmEvent } from "@/lib/abTest";
import { useInfiniteQuery } from "@tanstack/react-query";
import { getDiscoveryCafes } from "@/features/discovery/api/discoveryApi";
import { getImageUrl } from "@/common/utils/image";

export default function DiscoveryPage() {
  const router = useRouter();
  const loaderRef = useRef<HTMLDivElement>(null);

  // 무한 스크롤 데이터 조회
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    status,
  } = useInfiniteQuery({
    queryKey: ["discovery", "feeds"],
    queryFn: ({ pageParam = 0 }) => getDiscoveryCafes(pageParam, 15),
    getNextPageParam: (lastPage) => (lastPage.last ? undefined : lastPage.number + 1),
    initialPageParam: 0,
  });

  // Intersection Observer를 이용한 무한 스크롤 감지
  useEffect(() => {
    if (!hasNextPage || isFetchingNextPage) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          fetchNextPage();
        }
      },
      { threshold: 0.5 }
    );

    if (loaderRef.current) {
      observer.observe(loaderRef.current);
    }

    return () => observer.disconnect();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  // 머무른 시간 측정 (GTM)
  useEffect(() => {
    const startTime = Date.now();
    return () => {
      const dwellTime = Math.round((Date.now() - startTime) / 1000);
      if (dwellTime > 1) {
        pushGtmEvent('discovery_dwell_time', { duration_seconds: dwellTime });
      }
    };
  }, []);

  const handleImageClick = (cafeId: string) => {
    pushGtmEvent('discovery_item_click', { cafe_id: cafeId });
    router.push(`/cafes/${cafeId}`);
  };

  if (status === "pending") {
    return (
      <div className="h-full min-h-full bg-[#F7F7F5] p-4 columns-2 gap-4 space-y-4">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="break-inside-avoid w-full bg-gray-200 rounded-xl animate-pulse" style={{ height: i % 2 === 0 ? '200px' : '300px' }} />
        ))}
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        데이터를 불러오는 중 오류가 발생했습니다.
      </div>
    );
  }

  const allFeeds = data.pages.flatMap((page) => page.content);

  return (
    <div className="h-full min-h-full bg-[#F7F7F5] pb-24 font-pretendard">
      <div className="pt-6 px-4 pb-4"></div>

      <div className="px-4 columns-2 gap-4 space-y-4">
        {allFeeds.map((feed, index) => {
          // 디자인 가이드: 세로 사진은 2:3, 가로 사진은 1:1로 크롭
          // 현재 데이터의 원본 비율을 알 수 없으므로 index에 따라 패턴 적용
          const isTall = index % 3 === 0;
          
          // feed.image가 비어있을 경우 feed.thumbnailUrl을 폴백으로 사용
          const rawPath = feed.image || feed.thumbnailUrl;
          
          // 경로가 존재하고 외부 링크가 아니며 폴더 구분자(/)가 없는 경우 'cafe/' 접두사 추가
          // (CloudFront 구조상 폴더명이 필요할 수 있음)
          const formattedPath = rawPath && !rawPath.startsWith("http") && !rawPath.includes("/")
            ? `cafe/${rawPath}`
            : rawPath;

          return (
            <div 
              key={`${feed.cafeId}-${index}`} 
              className={`break-inside-avoid relative w-full rounded-xl overflow-hidden cursor-pointer shadow-sm active:scale-[0.98] transition-transform bg-[#F5F0E8] ${
                isTall ? "aspect-[2/3]" : "aspect-square"
              }`}
              onClick={() => handleImageClick(feed.cafeId)}
            >
              <Image 
                src={getImageUrl(formattedPath)} 
                alt="추천 카페"
                fill
                className="object-cover block" 
                priority={index < 4}
                unoptimized
              />
            </div>
          );
        })}
      </div>

      {/* 무한 스크롤 트리거 요소 */}
      <div ref={loaderRef} className="h-10 flex items-center justify-center mt-4">
        {isFetchingNextPage && (
          <div className="w-6 h-6 border-2 border-[#C3304F] border-t-transparent rounded-full animate-spin" />
        )}
      </div>
    </div>
  );
}

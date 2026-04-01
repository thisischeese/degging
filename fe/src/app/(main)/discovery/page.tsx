"use client";

import { useEffect, useRef, useMemo } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { pushGtmEvent, getAbGroup } from "@/lib/abTest";
import { useInfiniteQuery } from "@tanstack/react-query";
import { getDiscoveryCafes } from "@/features/discovery/api/discoveryApi";
import { getImageUrl } from "@/common/utils/image";
import { DiscoveryFeedItem } from "@/features/discovery/types";

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
      { 
        rootMargin: "800px",
        threshold: 0 
      }
    );

    if (loaderRef.current) {
      observer.observe(loaderRef.current);
    }

    return () => observer.disconnect();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  // 머무른 시간 측정 (GTM)
  useEffect(() => {
    const startTime = Date.now();
    const group = getAbGroup();
    return () => {
      const dwellTime = Math.round((Date.now() - startTime) / 1000);
      if (dwellTime > 1) {
        pushGtmEvent('discovery_dwell_time', { 
          duration_seconds: dwellTime,
          ab_group: group
        });
      }
    };
  }, []);

  const handleImageClick = (cafeId: string) => {
    const group = getAbGroup();
    pushGtmEvent('discovery_item_click', { 
      cafe_id: cafeId,
      ab_group: group
    });
    router.push(`/cafes/${cafeId}`);
  };

  // 데이터를 useMemo로 관리하여 불필요한 재계산 및 참조 변경 방지
  const allFeeds = useMemo(() => {
    return data?.pages.flatMap((page) => page.content) || [];
  }, [data]);

  // 데이터를 왼쪽과 오른쪽 열로 분해 (원천적으로 다른 열로 이동하지 않도록 고정)
  const [leftFeeds, rightFeeds] = useMemo(() => {
    const left: typeof allFeeds = [];
    const right: typeof allFeeds = [];
    allFeeds.forEach((feed, index) => {
      if (index % 2 === 0) left.push(feed);
      else right.push(feed);
    });
    return [left, right];
  }, [allFeeds]);

  if (status === "pending") {
    return (
      <div className="h-full min-h-full bg-[#F7F7F5] p-4 flex gap-4">
        <div className="flex-1 flex flex-col gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={`left-${i}`} className="w-full bg-gray-200 rounded-xl animate-pulse" style={{ height: i % 2 === 0 ? '200px' : '300px' }} />
          ))}
        </div>
        <div className="flex-1 flex flex-col gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={`right-${i}`} className="w-full bg-gray-200 rounded-xl animate-pulse" style={{ height: i % 2 === 0 ? '300px' : '200px' }} />
          ))}
        </div>
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

  return (
    <div className="h-full min-h-full bg-[#F7F7F5] pb-24 font-pretendard">
      <div className="pt-6 px-4 pb-4"></div>

      <div className="px-4 flex gap-4 pb-4">
        {/* 왼쪽 열 */}
        <div className="flex-1 flex flex-col gap-4">
          {leftFeeds.map((feed, idx) => (
            <DiscoveryItem 
              key={feed.cafeId} 
              feed={feed} 
              index={idx * 2} // 원래 전체 리스트에서의 인덱스 추정치 (패턴 유지용)
              onClick={handleImageClick}
            />
          ))}
        </div>

        {/* 오른쪽 열 */}
        <div className="flex-1 flex flex-col gap-4">
          {rightFeeds.map((feed, idx) => (
            <DiscoveryItem 
              key={feed.cafeId} 
              feed={feed} 
              index={idx * 2 + 1} 
              onClick={handleImageClick}
            />
          ))}
        </div>
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

// 개별 아이템 컴포넌트 추출 (코드 가독성 및 재사용성)
function DiscoveryItem({ 
  feed, 
  index, 
  onClick 
}: { 
  feed: DiscoveryFeedItem; 
  index: number; 
  onClick: (id: string) => void 
}) {
  const isTall = index % 3 === 0;
  const rawPath = feed.image || feed.thumbnailUrl;
  const formattedPath = rawPath && !rawPath.startsWith("http") && !rawPath.includes("/")
    ? `cafe/${rawPath}`
    : rawPath;

  return (
    <div 
      className={`relative w-full rounded-xl overflow-hidden cursor-pointer shadow-sm active:scale-[0.98] transition-all bg-[#F5F0E8] ${
        isTall ? "aspect-[2/3]" : "aspect-square"
      }`}
      onClick={() => onClick(feed.cafeId)}
    >
      <Image 
        src={getImageUrl(formattedPath)} 
        alt="추천 카페"
        fill
        sizes="(max-width: 768px) 50vw, 33vw"
        className="object-cover block" 
        priority={index < 4}
        unoptimized
      />
    </div>
  );
}

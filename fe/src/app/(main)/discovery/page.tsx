"use client";

import { useEffect } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { pushGtmEvent } from "@/lib/abTest";

// 테스트를 위한 임시 가짜 데이터 (Mock Data)
// 나중에 서버(AI)에서 받아올 예시 데이터
const MOCK_FEEDS = [
  { id: 1, cafeId: 101, src: "/images/discovery/mood1.jpg", type: "VERTICAL" },
  { id: 2, cafeId: 102, src: "/images/discovery/mood2.jpg", type: "HORIZONTAL" },
  { id: 3, cafeId: 103, src: "/images/discovery/mood1.jpg", type: "VERTICAL" },
  { id: 4, cafeId: 104, src: "/images/discovery/mood1.jpg", type: "VERTICAL" },
  { id: 5, cafeId: 105, src: "/images/discovery/mood2.jpg", type: "HORIZONTAL" },
  { id: 6, cafeId: 106, src: "/images/discovery/mood1.jpg", type: "VERTICAL" },
  { id: 7, cafeId: 107, src: "/images/discovery/mood2.jpg", type: "HORIZONTAL" },
  { id: 8, cafeId: 108, src: "/images/discovery/mood1.jpg", type: "VERTICAL" },
  { id: 9, cafeId: 109, src: "/images/discovery/mood2.jpg", type: "HORIZONTAL" },
];

export default function DiscoveryPage() {
  const router = useRouter();

  useEffect(() => {
    const startTime = Date.now();
    return () => {
      const dwellTime = Math.round((Date.now() - startTime) / 1000);
      if (dwellTime > 1) {
        pushGtmEvent('discovery_dwell_time', { duration_seconds: dwellTime });
      }
    };
  }, []);

  const handleImageClick = (cafeId: number) => {
    pushGtmEvent('discovery_item_click', { cafe_id: cafeId });
    router.push(`/cafes/${cafeId}`);
  };

  return (
    <div className="h-full min-h-full bg-[#F7F7F5] pb-24 font-pretendard">
      <div className="pt-6 px-4 pb-4">
      </div>

      {/* 
        Masonry(메이슨리) 레이아웃 핵심 구현부
        - columns-2: 모바일 환경이므로 세로를 2줄(2단)로 나눔
        - gap-4: 양옆, 위아래 간격을 16px(1rem)로 설정
      */}
      <div className="px-4 columns-2 gap-4 space-y-4">
        {MOCK_FEEDS.map((feed) => (
          <div 
            key={feed.id} 
            // break-inside-avoid: 이미지가 다음 단(column)으로 쪼개져서 넘어가는 것을 방지
            // 무조건 온전한 하나의 상자로 유지
            className="break-inside-avoid relative w-full rounded-xl overflow-hidden cursor-pointer shadow-sm active:scale-[0.98] transition-transform"
            onClick={() => handleImageClick(feed.cafeId)}
          >
            {/* 
              비율(세로/가로)에 상관없이 원본 이미지의 비율을 그대로 유지하면서 화면에 꽉 차게 보여줌.
              width, height 속성을 명시적으로 주지 않아도, tailwind의 w-full과 h-auto 형식을 활용.
              다만, next/image는 크기를 요구하므로, layout="responsive" 효과를 내기 위해
              여기서는 img 태그 역할의 일반 방식을 혼합하거나 sizes를 씀.
            */}
            <Image 
              src={feed.src} 
              alt={`추천 분위기 ${feed.id}`}
              // next/image (v13+)에서 가로세로 비율을 유동적으로 가져갈 때의 꼼수
              width={500} // 원본 화질 유지를 위한 넉넉한 픽셀 수 (비율 계산용)
              height={feed.type === 'VERTICAL' ? 700 : 400} // type을 참고해 비율 유추
              className="w-full h-auto object-cover block" 
              priority={feed.id <= 4} // 처음 보이는 상위 4개는 빨리 로딩할 수 있게 우선순위 부여
            />
          </div>
        ))}
      </div>
      
    </div>
  );
}

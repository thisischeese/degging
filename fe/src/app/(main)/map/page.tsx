'use client';

import React, { Suspense, useEffect } from 'react';
import { Search, LocateFixed } from 'lucide-react';
import { useSuspenseQuery } from '@tanstack/react-query';
import { Chip } from '@/common/components/Chip';
import BottomNav from '@/common/components/BottomNav';
import { useMapStore } from '@/store/useMapStore';

// === 더미 데이터 및 fetcher (useSuspenseQuery 용도) ===
interface Cafe {
  id: string;
  name: string;
  lat: number;
  lng: number;
}

const fetchCafes = async (): Promise<Cafe[]> => {
  // 실제 API 호출로 변경될 부분
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve([
        { id: '1', name: '카페 A', lat: 37.5665, lng: 126.978 },
        { id: '2', name: '카페 B', lat: 37.5651, lng: 126.977 },
      ]);
    }, 1000);
  });
};

const FILTER_OPTIONS = ['# 조용한', '# 우드톤', '# 힙한'];

function MapContent() {
  const { selectedFilters, toggleFilter, userLocation, setUserLocation } = useMapStore();

  // TanStack Query v5 suspense 쿼리
  const { data: cafes } = useSuspenseQuery({
    queryKey: ['map', 'cafes', selectedFilters],
    queryFn: fetchCafes,
  });

  // 초기 사용자 위치 셋업 (임시 중심점)
  useEffect(() => {
    if (!userLocation) {
      setUserLocation({ lat: 37.5665, lng: 126.978 }); // 서울 중심 (예시)
    }
  }, [userLocation, setUserLocation]);

  const handleLocateMe = () => {
    // 내 위치로 이동하는 로직
    setUserLocation({ lat: 37.5665, lng: 126.978 });
    alert('현재 위치로 이동합니다.');
  };

  return (
    // 전체 화면 지도를 위한 레이아웃
    <div className="relative w-full h-[100dvh] bg-gray-100 overflow-hidden text-gray-900">
      
      {/* 1. 배경 가짜 지도 영역 (실제로는 카카오맵 등 연동) */}
      {/* 지도 라이브러리가 추가될 경우 아래 div 자리에 지도가 렌더링 됩니다 */}
      <div className="absolute inset-0 z-0 flex items-center justify-center bg-[#E8E6E0]">
        <span className="text-gray-400 font-medium">지도 렌더링 영역</span>

        {/* 사용자 현재 위치 마커 (파란색 점) */}
        {userLocation && (
          <div className="absolute z-10 flex items-center justify-center top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
            <div className="w-5 h-5 bg-blue-500 border-2 border-white rounded-full shadow-md shadow-blue-500/50 relative">
              <div className="absolute inset-0 bg-blue-400 rounded-full animate-ping opacity-75"></div>
            </div>
          </div>
        )}

        {/* 불러온 카페 데이터 렌더링 마커 (예시) */}
        {cafes.map((cafe, i) => (
          <div 
            key={cafe.id} 
            className="absolute p-1 bg-white border border-gray-300 rounded shadow-sm text-[10px] font-bold z-10"
            style={{ top: `${40 + i * 10}%`, left: `${40 + i * 15}%` }} // 임의 위치
          >
            {cafe.name}
          </div>
        ))}
      </div>

      {/* 2. Top Section (검색바 & 필터) */}
      <div className="absolute top-0 inset-x-0 z-20 flex flex-col pt-safe-top">
        {/* Search Bar */}
        <div className="px-4 py-3">
          <div className="flex items-center gap-2 px-4 py-3 bg-white/90 backdrop-blur-md border border-gray-200 rounded-2xl shadow-sm shadow-gray-200/50">
            <Search className="w-5 h-5 text-gray-400" />
            <input 
              type="text" 
              placeholder="어떤 카페를 찾으시나요?" 
              className="flex-1 bg-transparent border-none outline-none text-[15px] placeholder:text-gray-400 font-medium font-pretendard"
            />
          </div>
        </div>

        {/* Filter Chips (가로 스크롤) */}
        <div className="px-4 pb-2 overflow-x-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
          <div className="flex items-center gap-2 w-max">
            {FILTER_OPTIONS.map((filter) => (
              <Chip
                key={filter}
                label={filter}
                variant="map"
                isActive={selectedFilters.includes(filter)}
                onClick={() => toggleFilter(filter)}
              />
            ))}
          </div>
        </div>
      </div>

      {/* 3. 내 위치 이동 버튼 (우측 하단) */}
      {/* 하단 네비게이션(BottomNav)이 h-16(64px)을 차지하므로, 그 위에 띄워야 함 (bottom-20) */}
      <button 
        type="button"
        onClick={handleLocateMe}
        className="absolute bottom-20 right-4 z-20 flex items-center justify-center w-12 h-12 bg-white rounded-full shadow-md text-gray-700 hover:bg-gray-50 transition-colors border border-gray-100"
        aria-label="내 위치 찾기"
      >
        <LocateFixed className="w-6 h-6" />
      </button>

      {/* 4. Bottom Section (고정 내비게이션바) */}
      {/* BottomNav 내부에 fixed/bottom-0 설정이 되어 있습니다 */}
      <BottomNav />
    </div>
  );
}

// Suspense 폴백 스켈레톤 (선택 사항)
function MapSkeleton() {
  return (
    <div className="relative w-full h-[100dvh] bg-[#E8E6E0] animate-pulse overflow-hidden">
      <div className="absolute top-0 inset-x-0 z-20 flex flex-col pt-safe-top px-4 py-3">
        <div className="w-full h-12 bg-white/60 rounded-2xl" />
        <div className="flex gap-2 mt-3">
          <div className="w-16 h-8 bg-white/60 rounded-full" />
          <div className="w-16 h-8 bg-white/60 rounded-full" />
          <div className="w-16 h-8 bg-white/60 rounded-full" />
        </div>
      </div>
      <BottomNav />
    </div>
  );
}

export default function MapPage() {
  return (
    <Suspense fallback={<MapSkeleton />}>
      <MapContent />
    </Suspense>
  );
}

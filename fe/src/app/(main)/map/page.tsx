'use client';

import React, { Suspense, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { Search, LocateFixed, Plus } from 'lucide-react';
import searchIcon from '@/assets/images/map/mapSearchIcon.png';
import tagPlusIcon from '@/assets/images/map/tagPlusIcon.png';
import recommendLogo from '@/assets/images/map/recommendLogo.png';
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
  isRecommend?: boolean;
}

const fetchCafes = async (): Promise<Cafe[]> => {
  // 실제 API 호출로 변경될 부분
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve([
        { id: '1', name: '카페 A', lat: 37.5665, lng: 126.978 },
        { id: '2', name: '카페 B', lat: 37.5651, lng: 126.977 },
        { id: '3', name: '씨티커피 역삼', lat: 37.5036601, lng: 127.0382947, isRecommend: true },
      ]);
    }, 1000);
  });
};

const FILTER_OPTIONS = ['# 조용한', '# 우드톤', '# 힙한'];

function MapContent() {
  const router = useRouter();
  const {
    selectedFilters,
    toggleFilter,
    userLocation,
    setUserLocation,
    isTracking,
    toggleTracking,
    setTracking
  } = useMapStore();

  // 1. 지도 인스턴스와 마커들을 관리할 Ref
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const userOverlayRef = useRef<any>(null);
  const watchIdRef = useRef<number | null>(null);


  // TanStack Query v5 suspense 쿼리
  const { data: cafes } = useSuspenseQuery({
    queryKey: ['map', 'cafes', selectedFilters],
    queryFn: fetchCafes,
  });

  // 0. 초기 진입 시 자동 현 위치 추적
  useEffect(() => {
    setTracking(true);
  }, [setTracking]);

  // 2. 지도 초기화 useEffect
  useEffect(() => {
    if (!window.kakao) return;

    window.kakao.maps.load(() => {
      if (!mapContainerRef.current) return;

      const center = userLocation
        ? new window.kakao.maps.LatLng(userLocation.lat, userLocation.lng)
        : new window.kakao.maps.LatLng(37.5665, 126.978);

      const options = {
        center,
        level: 3,
      };

      // 지도 생성
      mapInstance.current = new window.kakao.maps.Map(mapContainerRef.current, options);

      // 내 위치 마커(CustomOverlay) 초기화
      const overlayContent = document.createElement('div');
      overlayContent.className = 'w-4 h-4 bg-[#007EEB] rounded-full border-2 border-white shadow-[0_0_12px_rgba(0,126,235,0.6)]';

      userOverlayRef.current = new window.kakao.maps.CustomOverlay({
        position: center,
        content: overlayContent,
        map: null, // isTracking일 때만 활성화
      });
    });
  }, []); // 최초 1회 실행

  // 3. 카페 데이터가 변경될 때마다 마커 업데이트
  useEffect(() => {
    if (!mapInstance.current || !cafes) return;

    // 기존 마커 제거
    markersRef.current.forEach((marker) => marker.setMap(null));
    markersRef.current = [];

    // 새 마커 추가
    cafes.forEach((cafe) => {
      const markerPosition = new window.kakao.maps.LatLng(cafe.lat, cafe.lng);

      let markerOptions: any = {
        position: markerPosition,
        title: cafe.name,
      };

      if (cafe.isRecommend) {
        // 커스텀 브랜드 마커
        const imageSize = new window.kakao.maps.Size(24, 24);
        const markerImage = new window.kakao.maps.MarkerImage(recommendLogo.src, imageSize);
        markerOptions.image = markerImage;
        // zIndex 조절 등 부가 설정이 가능하다면 추가, 여기선 기본 마커 옵션에 병합
      }

      const marker = new window.kakao.maps.Marker(markerOptions);

      if (cafe.isRecommend) {
        window.kakao.maps.event.addListener(marker, 'click', () => {
          if (mapInstance.current) {
            mapInstance.current.panTo(markerPosition);
          }
          router.push(`/cafe/city-coffee-yeoksam`);
        });
      }

      marker.setMap(mapInstance.current);
      markersRef.current.push(marker);
    });
  }, [cafes, router]);

  // 4. 위치 추적 (watchPosition) 및 UI 동기화
  useEffect(() => {
    if (isTracking) {
      if (navigator.geolocation) {
        watchIdRef.current = navigator.geolocation.watchPosition(
          (position) => {
            const { latitude, longitude } = position.coords;
            const newPos = new window.kakao.maps.LatLng(latitude, longitude);

            setUserLocation({ lat: latitude, lng: longitude });

            if (mapInstance.current) {
              mapInstance.current.panTo(newPos); // 부드럽게 이동
            }
            if (userOverlayRef.current) {
              userOverlayRef.current.setPosition(newPos);
              userOverlayRef.current.setMap(mapInstance.current);
            }
          },
          (error) => {
            console.error('위치 정보를 가져올 수 없습니다.', error);
            setTracking(false);
          },
          { enableHighAccuracy: true, maximumAge: 0 }
        );
      } else {
        alert('이 브라우저에서는 위치 추적을 지원하지 않습니다.');
        setTracking(false);
      }
    } else {
      // 추적 해제 시 오버레이 숨김 및 watch 취소
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
        watchIdRef.current = null;
      }
      if (userOverlayRef.current) {
        userOverlayRef.current.setMap(null);
      }
    }

    return () => {
      // 컴포넌트 언마운트 시 watch 취소
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, [isTracking, setUserLocation, setTracking]);

  // 내 위치 버튼 핸들러 (토글)
  const handleLocateMe = () => {
    toggleTracking();
  };

  return (
    <div className="relative w-full h-[100dvh] bg-gray-100 overflow-hidden text-gray-900">

      {/* 실제 카카오맵이 렌더링될 영역 */}
      <div
        ref={mapContainerRef}
        className="absolute inset-0 z-0"
      />

      {/* UI Overlay: Top Section */}
      <div className="absolute top-0 inset-x-0 z-20 flex flex-col pt-safe-top">
        <div className="px-4 py-3 flex items-center gap-2">

          {/* 검색바 */}
          <div className="flex-1 h-10 flex items-center gap-2 px-3 bg-white/90 backdrop-blur-md border border-gray-200 rounded-[5px] shadow-sm">
            <Search className="w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="디저트 검색"
              className="flex-1 bg-transparent border-none outline-none text-[15px] placeholder:text-gray-400 font-medium font-pretendard"
            />
          </div>

          {/* 검색바 우측 우드톤 검색 버튼 */}
          <button className="flex-shrink-0 flex items-center justify-center w-10 h-10 bg-[#865B28] rounded-[5px] shadow-sm">
            <Image src={searchIcon} alt="검색" width={24} height={24} className="w-6 h-6 object-contain" />
          </button>
        </div>

        <div className="px-4 pb-2 flex items-center gap-2">
          {/* 가로 스크롤 고정 필터 추가 버튼 */}
          <button className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full bg-[#DBC9AD] shadow-sm">
            <Image src={tagPlusIcon} alt="태그 추가" width={20} height={20} className="w-5 h-5 object-contain" />
          </button>

          {/* 스크롤 가능한 칩 리스트 */}
          <div className="flex-1 overflow-x-auto no-scrollbar">
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
      </div>

      {/* 내 위치 이동 버튼 */}
      <button
        type="button"
        onClick={handleLocateMe}
        className={`absolute bottom-24 right-4 z-20 flex items-center justify-center w-12 h-12 bg-white rounded-full shadow-lg active:scale-95 transition-all border ${isTracking
          ? 'border-[#007EEB] text-[#007EEB]'
          : 'border-gray-100 text-gray-700 hover:bg-gray-50'
          }`}
      >
        <LocateFixed className="w-6 h-6" />
      </button>

      <BottomNav />
    </div>
  );
}

// 스켈레톤 유지
function MapSkeleton() {
  return (
    <div className="relative w-full h-[100dvh] bg-[#E8E6E0] animate-pulse overflow-hidden">
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
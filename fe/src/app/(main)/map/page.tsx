'use client';

import React, { Suspense, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { StaticImageData } from 'next/image';
import { Search, LocateFixed } from 'lucide-react';
import { motion, useAnimation } from 'framer-motion';
import { useSuspenseQuery } from '@tanstack/react-query';
import { Chip } from '@/common/components/Chip';
import { Dropdown } from '@/common/components/Dropdown';
import { CafeCard } from '@/common/components/CafeCard';
import BottomNav from '@/common/components/BottomNav';
import { useMapStore } from '@/store/useMapStore';

// === 더미 데이터 및 fetcher (useSuspenseQuery 용도) ===
interface Cafe {
  id: string;
  name: string;
  lat: number;
  lng: number;
  isRecommend?: boolean;
  imageUrl?: string | StaticImageData;
  description?: string;
  address?: string;
  distance?: string;
}

const fetchCafes = async (): Promise<Cafe[]> => {
  // 실제 API 호출로 변경될 부분
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve([
        {
          id: '1', name: '아우어베이커리 역삼점',
          lat: 37.502035,
          lng: 127.040018,
          isRecommend: true,
          imageUrl: "/images/cafe/cafe1.png",
          description: '조용하고 넓은 공간에서 즐기는 시그니처 빵',
          address: '서울 강남구 언주로85길 29 1층',
          distance: '99m'
        },
        {
          id: '2', name: '씨티커피 역삼',
          lat: 37.5036601,
          lng: 127.0382947,
          isRecommend: true,
          imageUrl: "/images/cafe/cafe2.png",
          description: '직장인들을 위한 최고의 휴식 공간',
          address: '서울 강남구 테헤란로 123',
          distance: '200m'
        },
        {
          id: '3', name: '씨티커피 역삼',
          lat: 37.5036,
          lng: 127.038,
          isRecommend: true,
          imageUrl: "/images/cafe/cafe2.png",
          description: '직장인들을 위한 최고의 휴식 공간',
          address: '서울 강남구 테헤란로 123',
          distance: '200m'
        },
        {
          id: '4', name: '씨티커피 역삼',
          lat: 37.6000,
          lng: 127.0444,
          isRecommend: true,
          imageUrl: "/images/cafe/cafe2.png",
          description: '직장인들을 위한 최고의 휴식 공간',
          address: '서울 강남구 테헤란로 123',
          distance: '200m'
        },
      ]);
    }, 1000);
  });
};

const FILTER_OPTIONS = ['# 조용한', '# 우드톤', '# 힙한'];

const SORT_OPTIONS = [
  { value: 'recommend', label: '추천순' },
  { value: 'rating', label: '별점순' },
  { value: 'review', label: '리뷰많은순' },
  { value: 'distance', label: '거리순' },
];

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

  const [isMapLoaded, setIsMapLoaded] = useState(false);
  const [isFranchiseIncluded, setIsFranchiseIncluded] = useState(false);
  const [sortBy, setSortBy] = useState('recommend');
  const [windowHeight, setWindowHeight] = useState(800);
  const [activeCafeId, setActiveCafeId] = useState<string | null>(null);
  // [수정] 최신 ID를 리스너에서 참조하기 위한 Ref
  const activeCafeIdRef = useRef<string | null>(null);
  useEffect(() => {
    activeCafeIdRef.current = activeCafeId;
  }, [activeCafeId]);
  const cardRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const controls = useAnimation();
  const initialUserLocationRef = useRef(userLocation);

  // 1. 지도 인스턴스와 마커들을 관리할 Ref
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<kakao.maps.Map | null>(null);
  const markersRef = useRef<kakao.maps.Marker[]>([]);
  const userOverlayRef = useRef<kakao.maps.CustomOverlay | null>(null);
  const watchIdRef = useRef<number | null>(null);
  // window height 관련 효과 최적화 (동기적 setState 방지)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const handleResize = () => setWindowHeight(window.innerHeight);
      handleResize(); // 초기값 설정
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
    }
  }, []);

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

      const initialUserLocation = initialUserLocationRef.current;
      const center = initialUserLocation
        ? new window.kakao.maps.LatLng(initialUserLocation.lat, initialUserLocation.lng)
        : new window.kakao.maps.LatLng(37.5665, 126.978);

      const options = {
        center,
        level: 3,
      };

      // 지도 생성
      mapInstance.current = new window.kakao.maps.Map(mapContainerRef.current, options);
      setIsMapLoaded(true);

      // 지도 빈 영역 클릭 시 선택 해제 및 바텀 시트 내리기
      window.kakao.maps.event.addListener(mapInstance.current, 'click', () => {
        setActiveCafeId(null);
        controls.start({ y: 0, transition: { type: "spring", stiffness: 300, damping: 30 } }); // 시트 원위치
      });

    });
  }, [controls]);

  // 3. 카페 데이터가 변경될 때마다 마커 업데이트 (지도가 로드된 상태 보장)
  useEffect(() => {
    if (!mapInstance.current || !cafes || !isMapLoaded) return;

    // 기존 마커 제거
    markersRef.current.forEach((marker) => marker.setMap(null));
    markersRef.current = [];

    // 공통 마커 이미지 설정 (루프 밖에서 한 번만 생성하여 성능 최적화)
    const imageSize = new window.kakao.maps.Size(24, 24);
    const markerImage = new window.kakao.maps.MarkerImage("/images/map/recommendLogo.png", imageSize);

    cafes.forEach((cafe) => {
      const markerPosition = new window.kakao.maps.LatLng(cafe.lat, cafe.lng);

      // 모든 마커에 커스텀 이미지 적용
      const markerOptions: kakao.maps.MarkerOptions = {
        position: markerPosition,
        title: cafe.name,
        image: markerImage,
        zIndex: cafe.isRecommend ? 10 : 1
      };
      const marker = new window.kakao.maps.Marker(markerOptions);

      // 클릭 이벤트: 공통적으로 지도를 해당 위치로 이동(panTo)
      window.kakao.maps.event.addListener(marker, 'click', () => {
        // [수정] Ref를 사용하여 최신 activeCafeId와 비교 (클로저 문제 해결)
        if (activeCafeIdRef.current === cafe.id) {
          setActiveCafeId(null);
          controls.start({ y: 0, transition: { type: "spring", stiffness: 300, damping: 30 } });
        } else {
          setActiveCafeId(cafe.id);
          
          const map = mapInstance.current;
          if (map) {
            map.panTo(markerPosition);
            setTimeout(() => {
              (map as unknown as { panBy: (dx: number, dy: number) => void }).panBy(0, 120); // 120px 정도 맵을 밀어 마커 위치 조정
            }, 100);
          }

          controls.start({ y: -180, transition: { type: "spring", stiffness: 300, damping: 30 } });
        }
      });

      marker.setMap(mapInstance.current);
      markersRef.current.push(marker);
    });
  }, [cafes, router, isMapLoaded, controls]);

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
              
              if (!userOverlayRef.current) {
                const el = document.createElement('div');
                el.className = 'w-5 h-5 bg-[#007EEB] border-[3px] border-white rounded-full shadow-[0_0_12px_4px_rgba(0,126,235,0.4)]';
                userOverlayRef.current = new window.kakao.maps.CustomOverlay({
                  position: newPos,
                  content: el,
                  zIndex: 20
                });
              }
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

  // activeCafeId 변경 시 바텀 시트 내 해당 카드로 자동 스크롤
  useEffect(() => {
    if (activeCafeId && cardRefs.current[activeCafeId] && scrollContainerRef.current) {
      const container = scrollContainerRef.current;
      const card = cardRefs.current[activeCafeId];
      if (card && container) {
        const containerTop = container.getBoundingClientRect().top;
        const cardTop = card.getBoundingClientRect().top;
        const scrollPos = container.scrollTop + (cardTop - containerTop) - 16; // 약간의 패딩 고려

        container.scrollTo({
          top: Math.max(0, scrollPos),
          behavior: 'smooth',
        });
      }
    }
  }, [activeCafeId]);

  // 내 위치 버튼 핸들러 (토글)
  const handleLocateMe = () => {
    toggleTracking();
  };

  // 카페 카드 클릭 핸들러
  const handleCafeClick = (cafe: Cafe) => {
    router.push(`/cafes/${cafe.id}`);
  };

  return (
    <div className="relative w-full h-[100dvh] bg-gray-100 overflow-hidden text-gray-900 font-pretendard">

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
            <Image src="/images/map/mapSearchIcon.png" alt="검색" width={24} height={24} className="w-6 h-6 object-contain" />
          </button>
        </div>

        <div className="px-4 pb-2 flex items-center gap-2">
          {/* 가로 스크롤 고정 필터 추가 버튼 */}
          <button className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full bg-[#DBC9AD] shadow-sm">
            <Image src="/images/map/tagPlusIcon.png" alt="태그 추가" width={20} height={20} className="w-5 h-5 object-contain" />
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
        className={`absolute bottom-[160px] right-4 z-20 flex items-center justify-center w-12 h-12 bg-white rounded-full shadow-lg active:scale-95 transition-all border ${isTracking
          ? 'border-[#007EEB] text-[#007EEB]'
          : 'border-gray-100 text-gray-700 hover:bg-gray-50'
          }`}
      >
        <LocateFixed className="w-6 h-6" />
      </button>

      {/* Framer-Motion Bottom Sheet */}
      <motion.div
        animate={controls}
        initial={{ y: 0 }}
        drag="y"
        dragConstraints={{ top: 240 - windowHeight, bottom: 0 }}
        dragElastic={0.1}
        dragMomentum={true}
        dragTransition={{ bounceStiffness: 200, bounceDamping: 25 }}
        className="absolute top-[calc(100dvh-140px)] inset-x-0 z-30 flex flex-col w-full h-[100dvh] bg-white rounded-t-[24px] shadow-[0_-8px_30px_rgba(0,0,0,0.12)] pb-[120px]"
      >
        <div className="w-full pt-3 pb-2 flex justify-center cursor-grab active:cursor-grabbing shrink-0">
          <div className="w-12 h-1.5 bg-gray-300 rounded-full" />
        </div>

        <div className="px-5 pb-3 pt-1 flex items-center justify-between border-b border-gray-100 shrink-0">
          <Dropdown
            options={SORT_OPTIONS}
            value={sortBy}
            onChange={setSortBy}
          />
          <Chip label="프차 포함" variant="map" isActive={isFranchiseIncluded} onClick={() => setIsFranchiseIncluded(!isFranchiseIncluded)} />
        </div>

        <div ref={scrollContainerRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-3 no-scrollbar relative">
          {cafes.map((cafe) => (
            <div key={cafe.id} ref={(el) => { cardRefs.current[cafe.id] = el; }}>
              <CafeCard
                id={cafe.id}
                name={cafe.name}
                description={cafe.description || ''}
                address={cafe.address || ''}
                distance={cafe.distance || ''}
                imageUrl={cafe.imageUrl || ''}
                isActive={activeCafeId === cafe.id}
                onClick={() => handleCafeClick(cafe)}
              />
            </div>
          ))}
        </div>
      </motion.div>

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

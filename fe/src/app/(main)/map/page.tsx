'use client';

import React, { Suspense, useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Image from 'next/image';
import { StaticImageData } from 'next/image';
import { Search, LocateFixed } from 'lucide-react';
import { motion, useAnimation } from 'framer-motion';
// 기존 코드 유지: import { useSuspenseQuery, useInfiniteQuery } from '@tanstack/react-query';
import { useQuery, useInfiniteQuery } from '@tanstack/react-query';
import { Chip } from '@/common/components/Chip';
import { Dropdown } from '@/common/components/Dropdown';
import { CafeCard } from '@/common/components/CafeCard';
import BottomNav from '@/common/components/BottomNav';
import { useMapStore } from '@/store/useMapStore';
import { getCafeMarkers, getCafeBottomSheetList } from '@/features/map/api/mapApi';
import { searchCafes } from '@/features/cafes/api/cafeApi';
import { getUserPreferences } from '@/features/users/api/userApi';
import { CafeMarker, CafeBottomSheetItem } from '@/features/map/types';
import { SearchCafeItem } from '@/features/cafes/types';

// const FILTER_OPTIONS = ['# 조용한', '# 우드톤', '# 힙한'];

const SORT_OPTIONS = [
  { value: 'RECOMMEND', label: '추천순' },
  { value: 'RATING', label: '별점순' },
  { value: 'REVIEW_COUNT', label: '리뷰많은순' },
  { value: 'DISTANCE', label: '거리순' },
];

const formatDistance = (meters: number) => {
  if (meters >= 1000) {
    return `${(meters / 1000).toFixed(1)}km`;
  }
  return `${meters}m`;
};

function MapContent({ initialCenter }: { initialCenter: { lat: number; lng: number } }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const keyword = searchParams.get('keyword') || '';
  
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
  const [sortBy, setSortBy] = useState('RECOMMEND');
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
  // [수정] 지도 중심 좌표 상태 추가 (API 호출용) - props로 받은 초기 위치를 사용
  const [mapCenter, setMapCenter] = useState(initialCenter);

  // [추가] 검색어 입력을 위한 로컬 상태
  const [inputValue, setInputValue] = useState(keyword);
  useEffect(() => {
    setInputValue(keyword);
  }, [keyword]);

  const executeSearch = () => {
    if (inputValue.trim()) {
      router.push(`/map?keyword=${encodeURIComponent(inputValue.trim())}`);
    } else {
      router.push(`/map`);
    }
  };

  const handleSearchKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      executeSearch();
    }
  };

  // [추가] 사용자 취향 태그 세팅
  const { data: userTags = [] } = useQuery<string[]>({
    queryKey: ['userPreferences'],
    queryFn: getUserPreferences,
  });

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

  // [수정] 통합 마커 쿼리: 키워드가 있으면 검색 API(searchCafes), 없으면 일반 마커 API 호출
  /* 기존 코드 주석 (캐시 문제 해결을 위해 수정)
  const { data: cafes, isLoading: isMapLoading } = useQuery({
    queryKey: ['map', 'markers', mapCenter.lat, mapCenter.lng, isFranchiseIncluded, keyword, selectedFilters],
    queryFn: async () => { ... }
  });
  */
  
  // [수정] 프차 토글 시(true/false) 항상 즉각적인 API 재호출과 UI 반응을 위해 
  // 1) isLoading 대신 isFetching 바인딩
  // 2) staleTime: 0 명시하여 캐시 재활용 방지 및 무조건 호출
  const { data: cafes, isFetching: isMapLoading } = useQuery({
    queryKey: ['map', 'markers', mapCenter.lat, mapCenter.lng, isFranchiseIncluded, keyword, selectedFilters],
    queryFn: async () => {
      if (keyword.trim()) {
        return searchCafes({
          keyword,
          latitude: mapCenter.lat,
          longitude: mapCenter.lng,
          mood: selectedFilters.length > 0 ? selectedFilters.map(f => f.replace('# ', '')) : undefined
        });
      } else {
        return getCafeMarkers({
          latitude: mapCenter.lat,
          longitude: mapCenter.lng,
          includeFranchise: isFranchiseIncluded,
          tags: selectedFilters.length > 0 ? selectedFilters.map(f => f.replace('# ', '')) : undefined
        });
      }
    },
    staleTime: 0, // 항상 최신 데이터 패칭 보장
  });

  const isSearchMode = keyword.trim().length > 0;
  
  // 마커를 그릴 데이터 배열 파싱 (타입 가드)
  // 기존 코드:
  // const markerItems = isSearchMode 
  //   ? (cafes as SearchCafeItem[]) 
  //   : (cafes as { markers: CafeMarker[]; filterTags: string[] }).markers;
  
  /* [AS-IS: 의존성 배열 경고 방지를 위해 주석 처리]
  const markerItems = isSearchMode 
    ? (cafes as SearchCafeItem[] || []) 
    : ((cafes as { markers: CafeMarker[]; filterTags: string[] })?.markers || []);
  */

  // [TO-BE] useMemo를 활용한 데이터 메모이제이션
  /* 기존 코드 주석 (API에서 filterTags 필드 삭제됨)
  const markerItems = React.useMemo(() => {
    return isSearchMode 
      ? (cafes as SearchCafeItem[] || []) 
      : ((cafes as { markers: CafeMarker[]; filterTags: string[] })?.markers || []);
  }, [isSearchMode, cafes]);
  */
  // [수정] filterTags 제거 반영된 타입 캐스팅
  const markerItems = React.useMemo(() => {
    return isSearchMode 
      ? (cafes as SearchCafeItem[] || []) 
      : ((cafes as { markers: CafeMarker[] })?.markers || []);
  }, [isSearchMode, cafes]);
    
  // 서버에서 받은 추천 필터 태그 (향후 UI 렌더링을 위해 추출)
  // 기존 코드 주석 (filterTags 삭제 반영)
  // const serverFilterTags = !isSearchMode 
  //   ? (cafes as { markers: CafeMarker[]; filterTags: string[] }).filterTags 
  //   : [];
  /* 
  const serverFilterTags = !isSearchMode 
    ? ((cafes as { markers: CafeMarker[]; filterTags: string[] })?.filterTags || [])
    : [];
  */
  
  // 혹시라도 향후 사용되거나 다른 부분에 의존성이 있을 수 있으므로 빈 배열로 폴백 처리
  const serverFilterTags: string[] = [];

  // [추가] 바텀시트 리스트 무한 스크롤 쿼리
  /* 기존 코드
  const {
    data: bottomSheetData,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading: isBottomSheetLoading
  } = useInfiniteQuery({ ... });
  */
  const {
    data: bottomSheetData,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading: isBottomSheetLoading
  } = useInfiniteQuery({
    queryKey: ['map', 'bottom-sheet', mapCenter.lat, mapCenter.lng, isFranchiseIncluded, sortBy, selectedFilters],
    queryFn: ({ pageParam = 0 }) => getCafeBottomSheetList({
      latitude: mapCenter.lat,
      longitude: mapCenter.lng,
      includeFranchise: isFranchiseIncluded,
      sort: sortBy as 'DISTANCE' | 'RATING' | 'REVIEW_COUNT' | 'RECOMMEND',
      tags: selectedFilters.length > 0 ? selectedFilters.map(f => f.replace('# ', '')) : undefined,
      page: pageParam,
      size: 10
    }),
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      return lastPage.last ? undefined : allPages.length;
    },
    enabled: !isSearchMode, // 검색 모드일 때는 무한 스크롤 API 비활성화
    staleTime: 0, // [수정] 프차 토글 시 즉시 호출 보장
  });

  // 검색 모드일 경우 검색된 cafes 자체를 바텀시트 리스트로 사용
  const bottomSheetItems = isSearchMode ? markerItems : (bottomSheetData ? bottomSheetData.pages.flatMap(page => page.content) : []);

  // [추가] 초기 검색 시 첫 번째 결과로 중심 이동시키기
  const prevKeywordRef = useRef(keyword);
  useEffect(() => {
    if (isSearchMode && markerItems && markerItems.length > 0 && mapInstance.current) {
      if (prevKeywordRef.current !== keyword) {
        const first = markerItems[0];
        const newPos = new window.kakao.maps.LatLng(first.latitude, first.longitude);
        mapInstance.current.setCenter(newPos);
        
        // [수정] 렌더링 도중 상태 변경(동기적 setState 에러) 방지를 위해 비동기 처리
        setTimeout(() => {
          setMapCenter({ lat: first.latitude, lng: first.longitude });
        }, 0);
        
        prevKeywordRef.current = keyword;
        controls.start({ y: -180, transition: { type: "spring", stiffness: 300, damping: 30 } }); // 시트 올리기
      }
    } else {
      prevKeywordRef.current = keyword; // 키워드가 지워졌거나 결과가 없을 때 동기화
    }
  }, [markerItems, keyword, controls, isSearchMode]);

  // [추가] 바텀시트 끝에 닿으면 다음 페이지 호출하는 스크롤 핸들러
  useEffect(() => {
    const handleScroll = () => {
      if (!scrollContainerRef.current) return;
      const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
      if (scrollTop + clientHeight >= scrollHeight - 50) {
        if (hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      }
    };

    const container = scrollContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll);
    }
    return () => {
      if (container) {
        container.removeEventListener('scroll', handleScroll);
      }
    };
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  // 0. 초기 진입 시 자동 현 위치 추적
  useEffect(() => {
    /* 기존 코드:
    setTracking(true);
    */
    // [수정] 지도 시점 유지가 필요한 경우 (세션에 좌표가 있는 경우), 우선 권한으로 현 위치 추적(오버라이드)을 방지
    const savedLat = sessionStorage.getItem('mapCenterLat');
    if (!savedLat) {
      setTracking(true);
    }
  }, [setTracking]);

  // 2. 지도 초기화 useEffect
  useEffect(() => {
    const initMap = () => {
      if (!mapContainerRef.current || !window.kakao) return;

      window.kakao.maps.load(() => {
        if (!mapContainerRef.current) return;

        const center = new window.kakao.maps.LatLng(initialCenter.lat, initialCenter.lng);

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

        // [추가] 이벤트 디바운싱: 지도의 중심 좌표 갱신 (API 호출 최적화)
        /* 기존 코드 주석 블록
        window.kakao.maps.event.addListener(mapInstance.current, 'dragend', () => { ... });
        window.kakao.maps.event.addListener(mapInstance.current, 'zoom_changed', () => { ... });
        */
        
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        let mapDebounceTimer: any;
        const handleMapMove = () => {
          if (!mapInstance.current) return;
          clearTimeout(mapDebounceTimer);
          mapDebounceTimer = setTimeout(() => {
            if (!mapInstance.current) return;
            const center = mapInstance.current.getCenter();
            const lat = center.getLat();
            const lng = center.getLng();
            setMapCenter({ lat, lng });

            // [추가] 지도 시점(위치) 유지 (세션 스토리지 저장)
            sessionStorage.setItem('mapCenterLat', String(lat));
            sessionStorage.setItem('mapCenterLng', String(lng));
          }, 300); // 300ms 디바운스
        };

        window.kakao.maps.event.addListener(mapInstance.current, 'dragend', handleMapMove);
        window.kakao.maps.event.addListener(mapInstance.current, 'zoom_changed', handleMapMove);
      });
    };

    if (window.kakao && window.kakao.maps) {
      initMap();
    } else {
      // afterInteractive 등으로 스크립트가 늦게 로드될 경우를 대비한 폴링
      const timer = setInterval(() => {
        if (window.kakao && window.kakao.maps) {
          clearInterval(timer);
          initMap();
        }
      }, 100);
      return () => clearInterval(timer);
    }
  }, [controls, initialCenter.lat, initialCenter.lng]);

  // 3. 카페 데이터가 변경될 때마다 마커 업데이트 (지도가 로드된 상태 보장)
  useEffect(() => {
    if (!mapInstance.current || !markerItems || !isMapLoaded) return;

    // 기존 마커 제거
    markersRef.current.forEach((marker) => marker.setMap(null));
    markersRef.current = [];

    // 공통 마커 이미지 설정 (루프 밖에서 한 번만 생성하여 성능 최적화)
    const imageSize = new window.kakao.maps.Size(24, 24);
    const markerImage = new window.kakao.maps.MarkerImage("/images/map/recommendLogo.png", imageSize);

    markerItems.forEach((cafe) => {
      // [수정] API 응답 타입의 latitude, longitude 사용
      const markerPosition = new window.kakao.maps.LatLng(cafe.latitude, cafe.longitude);

      // 모든 마커에 커스텀 이미지 적용
      const markerOptions: kakao.maps.MarkerOptions = {
        position: markerPosition,
        title: `카페 ID: ${cafe.cafeId}`, // name 속성이 API에 없으므로 cafeId 노출
        image: markerImage,
        zIndex: 1 // isRecommend 도 api에서 아직 안주므로 기본값
      };
      const marker = new window.kakao.maps.Marker(markerOptions);

      // 클릭 이벤트: 공통적으로 지도를 해당 위치로 이동(panTo)
      window.kakao.maps.event.addListener(marker, 'click', () => {
        // [수정] Ref를 사용하여 최신 activeCafeId와 비교 (클로저 문제 해결)
        if (activeCafeIdRef.current === cafe.cafeId) {
          setActiveCafeId(null);
          controls.start({ y: 0, transition: { type: "spring", stiffness: 300, damping: 30 } });
        } else {
          setActiveCafeId(cafe.cafeId);
          
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
  }, [markerItems, router, isMapLoaded, controls]);

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

  // 내 위치 버튼 핸들러 (현 위치 동기화 및 API 재호출)
  /* 기존 코드 주석 대상 
  const handleLocateMe = () => {
    ...
  };
  */
  const handleLocateMe = () => {
    // 1. 이미 사용자 위치(userLocation)가 상태로 존재한다면 GPS 지연 없이 즉시 이동
    if (userLocation && userLocation.lat !== 0 && mapInstance.current) {
      const newCenter = new window.kakao.maps.LatLng(userLocation.lat, userLocation.lng);
      mapInstance.current.panTo(newCenter);
      setMapCenter(userLocation);
      sessionStorage.setItem('mapCenterLat', String(userLocation.lat));
      sessionStorage.setItem('mapCenterLng', String(userLocation.lng));
      
      if (!isTracking) {
        setTracking(true);
      }
      return; // 브라우저 API 호출 생략 (딜레이/오류 제거)
    }

    // 2. 추적이 꺼져있었거나 첫 조회의 경우 강제 활성화 및 API 호출
    if (!isTracking) {
      setTracking(true);
    }

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const { latitude, longitude } = pos.coords;
          const lat = Number(latitude);
          const lng = Number(longitude);
          
          const newCenter = new window.kakao.maps.LatLng(lat, lng);

          if (mapInstance.current) {
            mapInstance.current.panTo(newCenter);
          }

          setMapCenter({ lat, lng });
          sessionStorage.setItem('mapCenterLat', String(lat));
          sessionStorage.setItem('mapCenterLng', String(lng));
          setUserLocation({ lat, lng });
        },
        (error) => {
          console.error("위치 정보를 가져올 수 없습니다.", error);
        },
        { enableHighAccuracy: true, maximumAge: 0 }
      );
    } else {
      alert("이 브라우저에서는 위치 추적을 지원하지 않습니다.");
    }
  };

  // 카페 카드 클릭 핸들러
  const handleCafeClick = (cafe: { cafeId: string }) => {
    router.push(`/cafes/${cafe.cafeId}`);
  };

  return (
    <div className="relative w-full h-[100dvh] bg-gray-100 overflow-hidden text-gray-900 font-pretendard">

      {/* 실제 카카오맵이 렌더링될 영역 */}
      <div
        ref={mapContainerRef}
        className="absolute inset-0 z-0"
      />

      {/* [최적화] 지도 데이터를 불러오는 중일 때 상단에 작은 스피너 표시 */}
      {isMapLoading && isMapLoaded && (
        <div className="absolute top-24 left-1/2 -translate-x-1/2 z-10 bg-white/90 backdrop-blur px-4 py-2 rounded-full shadow-md flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-gray-300 border-t-[#007EEB] rounded-full animate-spin" />
          <span className="text-xs text-gray-600 font-medium whitespace-nowrap">검색 중...</span>
        </div>
      )}

      {/* UI Overlay: Top Section */}
      <div className="absolute top-0 inset-x-0 z-20 flex flex-col pt-safe-top">
        <div className="px-4 py-3 flex items-center gap-2">

          {/* 검색바 (URL에서 키워드를 읽어와 표시) */}
          <div className="flex-1 h-10 flex items-center gap-2 px-3 bg-white/90 backdrop-blur-md border border-gray-200 rounded-[5px] shadow-sm">
            <Search className="w-5 h-5 text-gray-400" />
            {/* 기존 코드 보존:
            <input
              type="text"
              readOnly
              value={keyword}
              placeholder="디저트 검색"
              onClick={() => router.push('/')}
              className="flex-1 bg-transparent border-none outline-none text-[15px] text-gray-900 placeholder:text-gray-400 font-medium font-pretendard cursor-pointer"
            />
            */}
            {/* [수정] 입력 가능한 검색창으로 변경 및 핸들러 추가 */}
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleSearchKeyPress}
              placeholder="디저트 검색"
              className="flex-1 bg-transparent border-none outline-none text-[15px] text-gray-900 placeholder:text-gray-400 font-medium font-pretendard"
            />
          </div>

          {/* 검색바 우측 우드톤 검색 버튼 */}
          <button 
            onClick={executeSearch}
            className="flex-shrink-0 flex items-center justify-center w-10 h-10 bg-[#865B28] rounded-[5px] shadow-sm"
          >
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
              {/* 기존 코드 주석 보존
              {FILTER_OPTIONS.map((filter) => (
                <Chip
                  key={filter}
                  label={filter}
                  variant="map"
                  isActive={selectedFilters.includes(filter)}
                  onClick={() => toggleFilter(filter)}
                />
              ))}
              */}
              {userTags.map((tag) => {
                const filterLabel = `# ${tag}`; // 기존 로직과 동일하게 # 접두사 사용
                return (
                  <Chip
                    key={tag}
                    label={filterLabel}
                    variant="map"
                    isActive={selectedFilters.includes(filterLabel)}
                    onClick={() => toggleFilter(filterLabel)}
                  />
                );
              })}
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
          {isBottomSheetLoading ? (
            <div className="text-center py-10 font-medium text-gray-500 text-sm">로딩 중...</div>
          ) : bottomSheetItems.length === 0 ? (
            <div className="text-center py-10 font-medium text-gray-500 text-sm">해당 조건의 카페가 없습니다.</div>
          ) : (
            bottomSheetItems.map((cafe) => {
              // 타입 단언을 통해 any 키워드를 제거하고 명확한 인터페이스 활용
              const typedCafe = cafe as (CafeBottomSheetItem & SearchCafeItem);
              
              return (
                <div key={typedCafe.cafeId} ref={(el) => { cardRefs.current[typedCafe.cafeId] = el; }}>
                  {/* 기존 코드 보존:
                  <CafeCard
                    id={typedCafe.cafeId}
                    name={typedCafe.name || ''}
                    description={typedCafe.cafeIntro || ''}
                    address={typedCafe.roadAddress || typedCafe.address || ''}
                    distance=""
                    imageUrl={typedCafe.thumbnailUrl ? `${process.env.NEXT_PUBLIC_CLOUDFRONT_URL}/${typedCafe.thumbnailUrl}` : ''}
                    ...
                  />
                  */}
                  {/* [수정] distance 포매팅 적용 및 imageUrl 중복 방지 (가능하면 직접 사용, 필요시만 Cloudfront 결합) */}
                  <CafeCard
                    id={typedCafe.cafeId}
                    name={typedCafe.name || ''}
                    description={typedCafe.cafeIntro || ''}
                    address={typedCafe.roadAddress || typedCafe.address || ''}
                    distance={typedCafe.distance !== undefined ? formatDistance(typedCafe.distance) : ''}
                    imageUrl={
                      typedCafe.thumbnailUrl 
                        ? (typedCafe.thumbnailUrl.startsWith('http') 
                          ? typedCafe.thumbnailUrl 
                          : `${process.env.NEXT_PUBLIC_CLOUDFRONT_URL || ''}/${typedCafe.thumbnailUrl.startsWith('/') ? typedCafe.thumbnailUrl.slice(1) : typedCafe.thumbnailUrl}`) 
                        : ''
                    }
                    isScrapped={'isScrapped' in typedCafe ? typedCafe.isScrapped : false} // [추가] 스크랩 여부
                    isActive={activeCafeId === typedCafe.cafeId}
                    onClick={() => handleCafeClick(typedCafe)}
                  />
                </div>
              );
            })
          )}
          {isFetchingNextPage && (
            <div className="text-center py-4 text-gray-400 text-sm">더 불러오는 중...</div>
          )}
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
  /* 기존 코드 보존 (초기 로딩 시 지도 노출 방지)
  const [isLoadingLocation, setIsLoadingLocation] = useState(true);
  const [initialCenter, setInitialCenter] = useState({ lat: 37.5665, lng: 126.978 });
  const { setUserLocation } = useMapStore();

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = Number(pos.coords.latitude);
          const lng = Number(pos.coords.longitude);
          setInitialCenter({ lat, lng });
          setUserLocation({ lat, lng });
          setIsLoadingLocation(false);
        },
        (error) => {
          console.error("위치 정보를 가져올 수 없어 기본 좌표(서울역)로 설정합니다.", error);
          setIsLoadingLocation(false);
        },
        { enableHighAccuracy: true, maximumAge: 0, timeout: 5000 }
      );
    } else {
      setTimeout(() => setIsLoadingLocation(false), 0);
    }
  }, [setUserLocation]);

  if (isLoadingLocation) {
    return (
      <div className="relative w-full h-[100dvh] bg-[#E8E6E0] flex flex-col items-center justify-center overflow-hidden">
        <div className="flex flex-col items-center gap-4 text-gray-600">
          <div className="w-10 h-10 border-4 border-gray-300 border-t-[#007EEB] rounded-full animate-spin" />
          <p className="font-medium text-[15px] animate-pulse">내 위치를 찾는 중입니다...</p>
        </div>
        <BottomNav />
      </div>
    );
  }
  */

  // [최적화] 위치 정보를 기다리지 않고 즉시 기본 좌표로 지도 렌더링 (Non-blocking Location)
  // 이후 MapContent 컴포넌트 내부에서 위치 추적(watchPosition)을 통해 현재 위치로 자동 panTo 이동함.
  /* 기존 코드 주석 (단일 기본값 고정)
  const [initialCenter] = useState({ lat: 37.5665, lng: 126.978 });
  */
  
  // [수정] 카페 상세 페이지에서 돌아왔을 때의 지도 시점 유지 (State Persistence)
  const [initialCenter] = useState(() => {
    if (typeof window !== 'undefined') {
      const savedLat = sessionStorage.getItem('mapCenterLat');
      const savedLng = sessionStorage.getItem('mapCenterLng');
      if (savedLat && savedLng) {
        return { lat: Number(savedLat), lng: Number(savedLng) };
      }
    }
    // 기본 좌표 복구 (저장된 값 없을 때)
    return { lat: 37.5665, lng: 126.978 };
  });

  return (
    <Suspense fallback={<MapSkeleton />}>
      <MapContent initialCenter={initialCenter} />
    </Suspense>
  );
}

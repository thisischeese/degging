'use client';

import { useState, useRef, useEffect } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { Input } from "@/common/components/Input";
import { RankingItem } from "@/features/ranks/types";
import { pushGtmEvent, getAbGroup, setAbGroup } from "@/lib/abTest";
import searchIcon from "@/assets/icons/searchIcon.png";
import SurveyModal from "@/features/ranks/components/SurveyModal";
import { useQuery } from "@tanstack/react-query";
import { getRealTimeRankings } from "@/features/ranks/api/rankingApi";
import { QUERY_OPTIONS } from "@/common/components/providers/QueryProvider";
import { getUserInfo } from "@/features/users/api/userApi";

export default function MainPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [isSurveyOpen, setIsSurveyOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const startTime = Date.now();
    const timer = setTimeout(() => {
      // abGroup 상태를 여기서 세팅하던 로직은 activeGroup 변수로 대체되었습니다.
    }, 0);
    return () => {
      clearTimeout(timer);
      const dwellTime = Math.round((Date.now() - startTime) / 1000);
      if (dwellTime > 1) {
        pushGtmEvent('main_page_dwell_time', { duration_seconds: dwellTime });
      }
    };
  }, []);

  const [activeGroup, setActiveGroup] = useState<'A' | 'B' | null>(null);

  // 1. 초기 렌더링 시 로컬스토리지 값 사용 (깜빡임 최소화)
  useEffect(() => {
    const timer = setTimeout(() => {
      setActiveGroup(getAbGroup());
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  // 2. 백엔드 사용자 정보 조회 (DB에 저장된 abGroup 가져오기)
  const { data: profileData } = useQuery({
    queryKey: ["user", "me"],
    queryFn: getUserInfo,
    ...QUERY_OPTIONS.SENSITIVE,
  });

  // 3. 백엔드 응답이 오면 DB 값으로 로컬스토리지 덮어쓰기 및 화면 동기화
  useEffect(() => {
    if (profileData?.data?.abGroup) {
      const dbGroup = profileData.data.abGroup;
      setAbGroup(dbGroup);
      
      const timer = setTimeout(() => {
        setActiveGroup(dbGroup);
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [profileData]);

  // PC 환경 마우스 드래그 스크롤을 위한 상태

  // 스크롤이 될 박스(div) 자체를 가리키기 위한 용도
  const scrollRef = useRef<HTMLDivElement>(null);
  // "지금 마우스 왼쪽 버튼을 누른 채로 움직이고 있는가?"를 기억
  const isDragging = useRef(false);
  // 마우스를 딱 클릭했을 때의 X 좌표(가로 위치)를 기억
  const startX = useRef(0);
  // 마우스를 클릭했을 시점에, 스크롤이 이미 얼마나 넘어가 있었는지를 기억
  const scrollLeft = useRef(0);
  const isDragPassed = useRef(false); // 드래그 시 클릭 이벤트 방지

  const onDragStart = (e: React.MouseEvent) => {
    isDragging.current = true;
    isDragPassed.current = false;
    if (scrollRef.current) {
      startX.current = e.pageX - scrollRef.current.offsetLeft;
      scrollLeft.current = scrollRef.current.scrollLeft;
      // 드래그 시작 시 snap 속성 제거하여 부드럽게 움직이도록 함
      scrollRef.current.style.scrollSnapType = 'none';
    }
  };

  const onDragEnd = () => {
    isDragging.current = false;
    if (scrollRef.current) {
      // 드래그 종료 시 snap 속성 원상 복구
      scrollRef.current.style.scrollSnapType = 'x mandatory';
    }
  };

  const onDragMove = (e: React.MouseEvent) => {
    if (!isDragging.current || !scrollRef.current) return;
    
    e.preventDefault(); // 기본 드래그 동작 방지
    const x = e.pageX - scrollRef.current.offsetLeft;
    const walk = (x - startX.current) * 1.5; // 드래그 속도 조절 (1.5배)
    
    // 일정 픽셀 이상 움직였을 때만 드래그로 판정 (클릭과 구분)
    if (Math.abs(walk) > 5) {
      isDragPassed.current = true;
    }
    
    scrollRef.current.scrollLeft = scrollLeft.current - walk;
  };

  // 아이템 클릭 핸들러 (드래그 시 라우팅 방지)
  const handleItemClick = (e: React.MouseEvent, path: string, itemId: number) => {
    if (isDragPassed.current) {
      e.preventDefault();
      return;
    }
    pushGtmEvent('curation_click', { curation_id: itemId });
    router.push(path);
  };

  // 가짜 업데이트 시간 로직
  const getUpdateTime = () => {
    const now = new Date();
    const hours = now.getHours();
    const ampm = hours < 12 ? '오전' : '오후';
    const displayHours = hours % 12 || 12;
    return `${ampm} ${displayHours}:00 업데이트`;
  };

  // 검색 핸들러 (입력어 또는 랭킹 키워드로 이동)
  const handleSearch = (keyword?: string) => {
    const target = keyword || searchQuery;
    if (target.trim()) {
      pushGtmEvent('search_keyword', { keyword: target.trim() });
      router.push(`/map?keyword=${encodeURIComponent(target)}`);
    }
  };

  // 랭킹 데이터 조회 (React Query 연동)
  const { data: rankingData, isPending, isError } = useQuery({
    queryKey: ["rankings", "realtime"],
    queryFn: getRealTimeRankings,
    ...QUERY_OPTIONS.GENERAL,
  });

  // API 응답 구조에서 rankings 배열 추출 (데이터 로딩 전에는 빈 배열)
  const rankings: RankingItem[] = rankingData?.data.rankings || [];

  return (
    <div className="flex flex-col bg-bg_white font-pretendard overflow-x-hidden">
      
      {/* 검색 바: StepNickname의 Input 구조 + full 사이즈(h-42) 적용 */}
      <header className="px-6 pt-5 mb-4">
        <form onSubmit={(e) => { e.preventDefault(); handleSearch(); }}>
          <Input
            placeholder="'카공하기 좋은 카페'를 검색해보세요."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            // !를 사용하여 공통 Input의 기본 높이를 42px로 강제 고정
            className="h-[42px]! rounded-xl! bg-white! border-gray-200 shadow-sm text-sm pr-10!"
            rightElement={
              <button 
                type="submit" 
                className="p-2 mr-0.5 flex items-center justify-center active:scale-90 transition-transform"
              >
                <Image src={searchIcon} alt="검색" width={18} height={18} />
              </button>
            }
          />
        </form>
      </header>

      {/* 오늘의 큐레이션 참고: 가로 스크롤 & 나눔스퀘어 폰트 */}
      <section className="mb-7">
        <h2 className="px-7 text-lg font-bold text-gray-900 mb-3">오늘의 큐레이션</h2>
        <div 
          ref={scrollRef}
          onMouseDown={onDragStart}
          onMouseMove={onDragMove}
          onMouseUp={onDragEnd}
          onMouseLeave={onDragEnd}
          className="flex overflow-x-auto snap-x flex-nowrap snap-mandatory no-scrollbar gap-3 px-6"
        >
          {[1, 2, 3, 4, 5].map((item) => (
            <div 
              key={item} 
              className="relative flex-none shrink-0 w-[260px] h-[300px] snap-center rounded-[24px] overflow-hidden cursor-pointer shadow-sm select-none"
              onClick={(e) => handleItemClick(e, `/curations/${item}`, item)}
            >
              <Image draggable={false} src="/images/curation/mangoBingsu.png" alt="큐레이션" fill className="object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent flex flex-col justify-end p-5">
                {/* 큐레이션 내부는 나눔스퀘어 Bold 적용 */}
                <h3 className="text-white text-[17px] font-nanum_bold leading-tight tracking-tight">
                  무더위 날려버릴<br />완벽한 당도의 망고 빙수
                </h3>
              </div>
            </div>
          ))}
          {/* 오른쪽 끝 여백 유지를 위한 빈 박스 */}
          <div className="flex-none w-1" />
        </div>
      </section>

      {/* 이벤트 배너 영역 (설문조사 유도) */}
      <section className="px-6 mb-7">
        <div 
          onClick={() => setIsSurveyOpen(true)}
          className="bg-[#FCD82B] rounded-[24px] p-5 flex items-center justify-between cursor-pointer shadow-sm relative overflow-hidden active:scale-95 transition-transform"
        >
          <div className="flex flex-col z-10">
            <span className="text-black font-extrabold text-[16px] leading-tight">
              Degging 서비스 오픈 기념<br />설문하고 기프티콘 받자!
            </span>
            <span className="text-[#8B7404] text-[12px] font-bold mt-1.5 bg-white/40 px-2.5 py-1 rounded-md inline-block w-fit">
              최대 1만원 상당 디저트 지원
            </span>
          </div>
          <div className="text-5xl z-10">
            🎁
          </div>
          {/* Background decoration */}
          <div className="absolute right-[-10px] top-[-10px] w-24 h-24 bg-white opacity-20 rounded-full"></div>
          <div className="absolute right-[40px] bottom-[-20px] w-16 h-16 bg-white opacity-20 rounded-full"></div>
        </div>
      </section>

      {/* 인기 디저트 검색어: 비율 유지 및 세로 폭 확보 */}
      <section className="px-6 pb-24 w-full">
        <div className="flex items-end justify-between mb-3 px-2">
          <h2 className="text-lg font-bold text-gray-900 mb-1 leading-none">인기 디저트 검색어 랭킹</h2>
          <span className="text-[9px] text-gray-400 font-medium leading-none pr-2 mb-[-7px]">{getUpdateTime()}</span>
        </div>

        {/* 리스트 컨테이너 라운드 및 가로 길이에 비례하는 세로 비율(aspect-ratio) 고정. 
            flex-1 버그를 피하기 위해 inline style과 명시적 % 높이 사용 */}
        <div className="bg-white rounded-[24px] shadow-sm border border-gray-100 overflow-hidden px-1 h-auto min-h-[200px] flex flex-col justify-center">
          {isPending ? (
            // 1. 로딩 중: 스켈레톤 UI (반짝이는 애니메이션 효과)
            Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4 px-4 py-3.5 border-b border-gray-100 last:border-none animate-pulse">
                <div className="w-5 h-5 bg-gray-100 rounded-full" />
                <div className="flex-1 h-5 bg-gray-100 rounded-lg" />
                <div className="w-4 h-4 bg-gray-100 rounded" />
              </div>
            ))
          ) : isError ? (
            // 2. 에러 발생 시
            <div className="py-10 text-center">
              <p className="text-[13px] text-gray-400 font-medium">현재 랭킹 정보를 불러올 수 없습니다.</p>
              <p className="text-[11px] text-gray-300 mt-1">네트워크 상태를 확인해주세요.</p>
            </div>
          ) : rankings.length > 0 ? (
            // 3. 데이터가 있을 때만 렌더링
            rankings.slice(0, 5).map((item, index) => (
              <div 
                key={index}
                onClick={() => {
                  pushGtmEvent('ranking_click', { keyword: item.keyword, rank: item.rank });
                  handleSearch(item.keyword);
                }}
                className="flex items-center gap-4 px-4 py-3.5 border-b border-gray-50 last:border-none active:bg-gray-50 transition-colors cursor-pointer group"
              >
                <span className="w-5 text-center font-bold text-[#C3304F] text-[15px] shrink-0">
                  {index + 1}
                </span>
                <span className="flex-1 text-[15px] font-medium text-gray-800 truncate group-hover:text-[#C3304F] transition-colors">
                  {item.keyword}
                </span>
                <svg className="w-4 h-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 5l7 7-7 7" />
                </svg>
              </div>
            ))
          ) : (
            // 4. 데이터가 비어있을 때
            <div className="py-10 text-center text-[13px] text-gray-400">
              현재 검색 랭킹이 없습니다.
            </div>
          )}
        </div>
      </section>

      {/* 설문조사 모달 */}
      {isSurveyOpen && (
        <SurveyModal abGroup={activeGroup} onClose={() => setIsSurveyOpen(false)} />
      )}
    </div>
  );
}
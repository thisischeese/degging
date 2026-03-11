'use client';

import { useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { Input } from "@/common/components/Input";
import { RankingItem } from "@/features/ranks/types";
import mangoBingsuImg from "@/assets/images/curation/mangoBingsu.png";
import searchIcon from "@/assets/icons/searchIcon.png";

export default function MainPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const router = useRouter();

  // 1. 가짜 업데이트 시간 로직
  const getUpdateTime = () => {
    const now = new Date();
    const hours = now.getHours();
    const ampm = hours < 12 ? '오전' : '오후';
    const displayHours = hours % 12 || 12;
    return `${ampm} ${displayHours}:00 업데이트`;
  };

  // 2. 검색 핸들러 (입력어 또는 랭킹 키워드로 이동)
  const handleSearch = (keyword?: string) => {
    const target = keyword || searchQuery;
    if (target.trim()) {
      router.push(`/map?keyword=${encodeURIComponent(target)}`);
    }
  };

  // 3. 랭킹 데이터 (정의한 타입 적용)
  const rankings: RankingItem[] = [
    { rank: 1, keyword: "두쫀득" },
    { rank: 2, keyword: "던킨 두바이 먼치킨" },
    { rank: 3, keyword: "초코 소금빵" },
    { rank: 4, keyword: "바나나 크림 머시기" },
    { rank: 5, keyword: "딸기 빙수" },
  ];

  return (
    <div className="flex flex-col bg-bg_white font-pretendard">
      
      {/* 1. 검색 바: StepNickname의 Input 구조 + full 사이즈(h-42) 적용 */}
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

      {/* 2. 오늘의 큐레이션: 가로 스크롤 & 나눔스퀘어 폰트 */}
      <section className="mb-7">
        <h2 className="px-7 text-lg font-bold text-gray-900 mb-3">오늘의 큐레이션</h2>
        <div className="flex overflow-x-auto snap-x snap-mandatory no-scrollbar gap-3 px-6">
          {[1, 2, 3].map((item) => (
            <div 
              key={item} 
              className="relative flex-none w-[260px] h-[300px] snap-center rounded-[24px] overflow-hidden cursor-pointer shadow-sm"
              onClick={() => router.push(`/curation/detail`)}
            >
              <Image src={mangoBingsuImg} alt="큐레이션" fill className="object-cover" />
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

      {/* 3. 인기 디저트 검색어: 비율 유지 및 세로 폭 확보 */}
      <section className="px-6 pb-6">
        <div className="flex items-end justify-between mb-3 px-2">
          <h2 className="text-lg font-bold text-gray-900 mb-1 leading-none">인기 디저트 검색어 랭킹</h2>
          <span className="text-[9px] text-gray-400 font-medium leading-none pr-2 mb-[-7px]">{getUpdateTime()}</span>
        </div>

        {/* 리스트 컨테이너 라운드 및 가로 길이에 비례하는 세로 비율(aspect-ratio) 고정. 
            flex-1 버그를 피하기 위해 inline style과 명시적 % 높이 사용 */}
        <div 
          className="bg-white rounded-[24px] shadow-sm border border-gray-100 overflow-hidden px-1"
          style={{ aspectRatio: '310 / 218' }}
        >
          {rankings.map((item, index) => (
            <div 
              key={index}
              onClick={() => handleSearch(item.keyword)}
              className={`flex items-center justify-between px-5 w-full h-[46px] cursor-pointer active:bg-gray-50 transition-colors ${
                index !== rankings.length - 1 ? 'border-b border-gray-50' : ''
              }`}
            >
              <div className="flex items-center gap-4">
                <span className="text-xs font-bold text-gray-400 w-3 text-center">{item.rank}</span>
                <span className="text-[13px] text-gray-700 font-medium tracking-tight">{item.keyword}</span>
              </div>
              {/* 우측 화살표 아이콘 */}
              <svg width="5" height="8" viewBox="0 0 6 10" fill="none" className="mr-1">
                <path d="M1 9L5 5L1 1" stroke="#D1D1D1" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
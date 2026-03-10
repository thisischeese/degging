'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Image from 'next/image';

// 1. 파일명 정확히 임포트 (I 대문자 확인)
import HomeIcon from '@/assets/icons/homeIcon.png';      
import LocationIcon from '@/assets/icons/locationIcon.png'; 
import SearchIcon from '@/assets/icons/searchIcon.png';    
import BookmarkIcon from '@/assets/icons/bookmarkIcon.png'; 
import UserIcon from '@/assets/icons/userIcon.png';

// 각 아이콘별로 #C3304F로 변환하기 위한 최적의 필터 값입니다.
const NAV_ITEMS = [
   { 
     name: '메인 화면', 
     path: '/', 
     icon: HomeIcon,
    // Home 아이콘용 필터
    activeFilter: 'brightness-0 invert-[20%] sepia-[100%] saturate-[5000%] hue-rotate-[340deg]'
    },
  { 
    name: '지도', 
    path: '/map', 
    icon: LocationIcon,
    // Location 아이콘용 필터 (약간의 조정)
    activeFilter: 'brightness-0 invert-[40%] sepia-[50%] saturate-[3000%] hue-rotate-[0deg] brightness-[110%]'   },
   { 
     name: '탐색', 
     path: '/discovery', 
     icon: SearchIcon,
     // Search 아이콘용 필터 (약간의 조정)
    activeFilter: 'brightness-0 invert-[26%] sepia-[75%] saturate-[3453%] hue-rotate-[331deg] brightness-[89%] contrast-[86%]'   },
   { 
     name: '스크랩', 
     path: '/scrap', 
     icon: BookmarkIcon,
     // Bookmark 아이콘용 필터 (약간의 조정)
     activeFilter: 'brightness-0 invert-[29%] sepia-[90%] saturate-[2600%] hue-rotate-[328deg] brightness-[86%] contrast-[102%]'
   },
   { 
    name: '마이페이지', 
    path: '/user', 
    icon: UserIcon,
    // User 아이콘용 필터 (약간의 조정)
    activeFilter: 'brightness-0 invert-[30%] sepia-[80%] saturate-[2000%] contrast-[150%]'
  },
];

export default function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 z-50 h-16 w-full max-w-[inherit] border-t border-gray-100 bg-white px-2">
      <div className="flex h-full items-center justify-around">
        {NAV_ITEMS.map((item) => {
          // 현재 경로와 메뉴의 경로가 일치하는지 확인
          const isActive = pathname === item.path;

          return (
            <Link 
              key={item.path} 
              href={item.path} 
              className="flex flex-col items-center gap-1 flex-1" // flex-1을 주어 클릭 영역을 넓혔습니다.
            >
              <div className="relative h-6 w-6">
                <Image
                  src={item.icon}
                  alt={item.name}
                  width={24}
                  height={24}
                  className={`object-contain transition-all ${
                    // 활성화 상태면 빨간색(필터), 아니면 흐린 회색
                    isActive ? item.activeFilter : 'opacity-40'
                  }`}
                />
              </div>
              <span className={`text-[10px] ${
                isActive ? 'text-primary_btn_red font-bold' : 'text-gray-400'
              }`}>
                {item.name}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
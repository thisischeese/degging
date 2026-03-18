'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Image, { StaticImageData } from 'next/image';

// 아이콘 임포트
import HomeIcon from '@/assets/icons/homeIcon.png';
import HomeSelectedIcon from '@/assets/icons/homeSelectedIcon.png';
import LocationIcon from '@/assets/icons/locationIcon.png';
import LocationSelectedIcon from '@/assets/icons/locationSelected.png'; // 예외 케이스 반영
import SearchIcon from '@/assets/icons/searchIcon.png';
import SearchSelectedIcon from '@/assets/icons/searchSelectedIcon.png';
import BookmarkIcon from '@/assets/icons/bookmarkIcon.png';
import BookmarkSelectedIcon from '@/assets/icons/bookmarkSelectedIcon.png';
import UserIcon from '@/assets/icons/userIcon.png';
import UserSelectedIcon from '@/assets/icons/userSelectedIcon.png';

// 메뉴 데이터 인터페이스 정의
interface NavItem {
  name: string;
  path: string;
  icon: StaticImageData;
  selectedIcon: StaticImageData;
}

// 메뉴 데이터 관리
const NAV_ITEMS: NavItem[] = [
  {
    name: '메인 화면',
    path: '/',
    icon: HomeIcon,
    selectedIcon: HomeSelectedIcon,
  },
  {
    name: '지도',
    path: '/map',
    icon: LocationIcon,
    selectedIcon: LocationSelectedIcon,
  },
  {
    name: '탐색',
    path: '/discovery',
    icon: SearchIcon,
    selectedIcon: SearchSelectedIcon,
  },
  {
    name: '스크랩',
    path: '/scraps',
    icon: BookmarkIcon,
    selectedIcon: BookmarkSelectedIcon,
  },
  {
    name: '마이페이지',
    path: '/users',
    icon: UserIcon,
    selectedIcon: UserSelectedIcon,
  },
];

export default function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-1/2 z-50 h-16 w-full max-w-[375px] -translate-x-1/2 border-t border-gray-100 bg-white px-2 shadow-[0_-1px_10px_rgba(0,0,0,0.05)]">
      <div className="flex h-full items-center justify-around">
        {NAV_ITEMS.map((item) => {
          // /cafes/* 경로는 지도(/map) 탭을 활성화
          const cafePageActiveMap = pathname.startsWith('/cafes') ? '/map' : null;

          const isActive = item.path === '/'
            ? pathname === '/'
            : cafePageActiveMap === item.path || pathname.startsWith(item.path);

          return (
            <Link key={item.path} href={item.path} className="flex flex-col items-center gap-1 flex-1">
              <div className="relative h-6 w-6 flex items-center justify-center">
                <Image
                  src={isActive ? item.selectedIcon : item.icon}
                  alt={item.name}
                  fill // 부모 요소(h-6 w-6 relative div)를 꽉 채움
                  className="object-contain transition-all" // 비율 유지 + 중앙 정렬 + 깨짐 방지
                />
              </div>
              <span className={`text-[10px] ${isActive ? 'text-[#C3304F] font-bold' : 'text-gray-400'
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
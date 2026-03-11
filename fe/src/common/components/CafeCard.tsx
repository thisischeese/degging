import React from 'react';
import Image from 'next/image';
import { StaticImageData } from 'next/image';
import { MapPin, Star } from 'lucide-react';
import defaultCafe from '@/assets/images/cafe/baseCafeImage.png';

export interface CafeCardProps {
  id: string;
  name: string;
  description: string;
  address: string;
  distance?: string;
  imageUrl: string | StaticImageData;
  // isScrapped?: boolean;
  // onScrapClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  onClick?: () => void;
}

export const CafeCard = ({
  id,
  name,
  description,
  address,
  distance,
  imageUrl,
  // isScrapped = false,
  // onScrapClick,
  onClick,
}: CafeCardProps) => {
  // 스크랩 버튼 클릭 시 부모(카드) 클릭 이벤트 전달 차단
  // const handleScrapClick = (e: React.MouseEvent<HTMLButtonElement>) => {
  //   e.stopPropagation();
  //   onScrapClick?.(e);
  // };

  return (
    <div
      onClick={onClick}
      className="w-full font-pretendard flex p-4 bg-white border border-gray-200 rounded-2xl cursor-pointer hover:bg-gray-50 transition-colors gap-4"
    >
      {/* 1. 좌측 이미지 영역: 80x80 크기, rounded-xl */}
      <div className="relative w-20 h-20 shrink-0">
        <Image
          src={imageUrl || defaultCafe}
          alt={name}
          fill
          className="rounded-xl object-cover"
          unoptimized
        />
      </div>

      {/* 2. 우측 정보 영역: 말줄임(truncate) 처리를 고려한 flex 컨테이너 */}
      <div className="flex flex-col flex-1 min-w-0 justify-center">
        {/* 카페 이름 및 스크랩 아이콘 컨테이너 */}
        <div className="flex justify-between items-start gap-2">
          {/* 타이틀: font-bold, 크기 14px */}
          <h3 className="font-bold text-[14px] text-gray-900 truncate">
            {name}
          </h3>

          {/* {onScrapClick && (
            <button
              type="button"
              onClick={handleScrapClick}
              className="shrink-0 -mr-1 -mt-1 p-1 text-gray-400 hover:text-yellow-400 transition-colors"
              aria-label={isScrapped ? '스크랩 해제' : '스크랩 하기'}
            >
              <Star
                size={18}
                className={`transition-colors ${
                  isScrapped ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
                }`}
              />
            </button>
          )} */}
        </div>

        {/* 한 줄 설명: 크기 12px, 말줄임 */}
        <p className="text-[12px] text-gray-600 truncate mt-0.5 sm:mt-1">
          {description}
        </p>

        {/* 주소 및 아이콘 (+ 거리 텍스트 결합부) */}
        <div className="flex items-center text-gray-600 mt-auto pt-2">
          <MapPin size={14} className="shrink-0 mr-1" />
          <span className="text-[12px] truncate">{address}</span>
          {distance && (
            <>
              {/* 시각적 구분자 */}
              <span className="mx-1.5 text-[10px] text-gray-300 font-light">
                |
              </span>
              <span className="text-[12px] shrink-0 font-medium text-gray-500">
                {distance}
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

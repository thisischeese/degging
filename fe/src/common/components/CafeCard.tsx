import React, { useState } from 'react';
import Image, { StaticImageData } from 'next/image';
import { MapPin } from 'lucide-react';

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
  isActive?: boolean;
}

// 카페 카드에서 사용할 기본 이미지를 정의합니다.
const FALLBACK_CAFE_IMAGE = '/images/cafe/baseCafeImage.png';

export const CafeCard = React.forwardRef<HTMLDivElement, CafeCardProps>(({
  //  id, // 사용되지 않는 값 주석
  name,
  description,
  address,
  distance,
  imageUrl,
  onClick,
  isActive,
}, ref) => {
  // 스크랩 버튼 클릭 시 부모(카드) 클릭 이벤트 전달 차단
  // const handleScrapClick = (e: React.MouseEvent<HTMLButtonElement>) => {
  //   e.stopPropagation();
  //   onScrapClick?.(e);
  // };
  // 카페 카드에서 실패한 원격 이미지 URL을 기억합니다.
  const [failedImageUrl, setFailedImageUrl] = useState<string | null>(null);

  // 현재 렌더링에 사용할 카페 이미지를 계산합니다.
  const resolvedImageUrl =
    typeof imageUrl === 'string' && failedImageUrl === imageUrl
      ? FALLBACK_CAFE_IMAGE
      : imageUrl || FALLBACK_CAFE_IMAGE;

  return (
    <div
      ref={ref}
      onClick={onClick}
      className={`box-border w-full font-pretendard flex gap-4 rounded-2xl bg-white p-4 transition-all ${isActive
          ? 'ring-2 ring-inset ring-[#865B28] shadow-md'
          : 'border border-gray-200 hover:bg-gray-50'
        } ${onClick ? 'cursor-pointer' : ''}`}
    >
      {/* 카페 대표 이미지를 표시합니다. */}
      <div className="relative h-20 w-20 shrink-0">
        <Image
          src={resolvedImageUrl || FALLBACK_CAFE_IMAGE}
          alt={name}
          fill
          className="rounded-xl object-cover"
          unoptimized
          onError={() => {
            if (typeof imageUrl === 'string') {
              setFailedImageUrl(imageUrl);
            }
          }}
        />
      </div>

      {/* 카페 텍스트 정보를 표시합니다. */}
      <div className="flex min-w-0 flex-1 flex-col justify-center">
        <div className="flex items-start justify-between gap-2">
          <h3 className="truncate text-[14px] font-bold text-gray-900">{name}</h3>
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
          {distance ? (
            <>
              {/* 시각적 구분자 */}
              <span className="mx-1.5 text-[10px] text-gray-300 font-light">
                |
              </span>
              <span className="text-[12px] shrink-0 font-medium text-gray-500">
                {distance}
              </span>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
});
CafeCard.displayName = 'CafeCard';

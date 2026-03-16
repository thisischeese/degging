'use client';

import React, { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';

interface CafeDetail {
  id: string;
  name: string;
  description: string;
  rating: number;
  reviewCount: number;
  businessHours: string;
  address: string;
  phone: string;
  imageUrls: string[];
  menuList: { name: string; price: string; imageUrl: string }[];
}

const mockFetchDetail = async (cafeid: string): Promise<CafeDetail> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        id: cafeid,
        name: "아우어베이커리 역삼점",
        description: "더티초코, 빨미까레 등의 시그니처 메뉴와 특색 있는 경험을 파는 공간",
        rating: 3.8,
        reviewCount: 417,
        businessHours: "영업 중 12:00 ~ 24:00",
        address: "서울 마포구 포은로 63 형섭빌딩 2층",
        phone: "0503-7152-6912",
        imageUrls: [
          "/images/cafe/cafe1.png",
          "/images/cafe/cafe2.png",
          "/images/cafe/cafe1.png",
        ],
        menuList: [
          { name: "빨미까레", price: "5,500원", imageUrl: "/images/cafe/cafeMenu1.png" },
          { name: "더티초코", price: "5,800원", imageUrl: "/images/cafe/cafeMenu2.png" },
          { name: "빨미까레", price: "5,500원", imageUrl: "/images/cafe/cafeMenu1.png" },
        ]
      });
    }, 500);
  });
};

export default function CafeDetailPage({ params }: { params: Promise<{ cafeid: string }> | { cafeid: string } }) {
  const router = useRouter();
  const [cafe, setCafe] = useState<CafeDetail | null>(null);

  // Slider State
  const [currentIndex, setCurrentIndex] = useState(0);
  const [direction, setDirection] = useState(0);

  // React 18/19 compatibility for params (Next.js 15+ provides it as a Promise, older as an object)
  const resolvedParams = params instanceof Promise ? use(params) : params;
  const cafeid = resolvedParams.cafeid;

  useEffect(() => {
    if (cafeid) {
      mockFetchDetail(cafeid).then(setCafe);
    }
  }, [cafeid]);

  if (!cafe) {
    return (
      <div className="w-full h-[100dvh] flex items-center justify-center bg-bg_white text-gray-500 font-pretendard">
        로딩 중...
      </div>
    );
  }

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="w-full min-h-full bg-white font-pretendard flex flex-col pt-safe-top pb-8"
    >
      {/* 상단 비주얼 영역 (슬라이더) */}
      <div className="relative w-full h-[360px] shrink-0 overflow-hidden touch-pan-y bg-gray-100">
        <AnimatePresence initial={false} custom={direction}>
          <motion.div
            key={currentIndex}
            custom={direction}
            variants={{
              enter: (dir: number) => ({
                x: dir > 0 ? 100 : -100,
                opacity: 0,
                zIndex: 1, // 새 이미지는 위로
              }),
              center: {
                zIndex: 1,
                x: 0,
                opacity: 1,
              },
              exit: (dir: number) => ({
                zIndex: 0, // 이전 이미지는 뒤로
                x: dir > 0 ? -50 : 50, // 조금 덜 이동해서 오버랩 강조
                opacity: 0, // 서서히 뒷 배경으로 사라짐
              }),
            }}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{
              x: { type: "spring", stiffness: 300, damping: 30 },
              opacity: { duration: 0.3 },
            }}
            className="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing"
            drag="x"
            dragConstraints={{ left: 0, right: 0 }}
            dragElastic={0.2}
            onDragEnd={(e, { offset, velocity }) => {
              const swipe = offset.x;
              // velocity를 고려하거나 offset 민감도 조절
              if (swipe < -50 || velocity.x < -500) {
                // Next image (Swipe Left)
                setDirection(1);
                setCurrentIndex((prev) => (prev + 1) % cafe.imageUrls.length);
              } else if (swipe > 50 || velocity.x > 500) {
                // Previous image (Swipe Right)
                setDirection(-1);
                setCurrentIndex((prev) => (prev - 1 + cafe.imageUrls.length) % cafe.imageUrls.length);
              }
            }}
          >
            <Image
              src={cafe.imageUrls[currentIndex]}
              alt={`${cafe.name} 이미지 ${currentIndex + 1}`}
              fill
              className="object-cover pointer-events-none"
              draggable={false}
              priority={currentIndex === 0}
            />
          </motion.div>
        </AnimatePresence>

        {/* 뒤로가기 버튼 */}
        <button
          onClick={() => router.back()}
          className="absolute top-4 left-4 z-20 w-10 h-10 flex items-center justify-center cursor-pointer hover:opacity-80 transition-opacity pointer-events-auto"
        >
          <Image src="/images/map/backIcon.png" alt="뒤로가기" width={40} height={40} className="w-10 h-10 object-contain drop-shadow-md pointer-events-none" draggable={false} />
        </button>

        {/* 스크랩(별) 버튼 */}
        <button
          className="absolute top-4 right-4 z-20 w-10 h-10 flex items-center justify-center cursor-pointer hover:opacity-80 transition-opacity pointer-events-auto"
        >
          <Image src="/images/map/unscrappedIcon.png" alt="스크랩" width={40} height={40} className="w-10 h-10 object-contain drop-shadow-md pointer-events-none" draggable={false} />
        </button>

        {/* 하단 그라데이션 및 정보 오버레이 (고정) */}
        <div className="absolute inset-x-0 bottom-0 h-48 bg-gradient-to-t from-black/80 to-transparent flex flex-col justify-end px-5 pb-8 text-white z-10 pointer-events-none">
          <h1 className="text-[24px] font-semibold mb-2">{cafe.name}</h1>
          <p className="text-[14px] text-gray-200 leading-snug w-[90%]">{cafe.description}</p>
        </div>

        {/* 인디케이터 (페이지네이션 도트) - 동적 렌더링 */}
        <div className="absolute bottom-4 inset-x-0 flex justify-center items-center gap-1.5 z-20 pointer-events-none">
          {cafe.imageUrls.map((_, idx) => (
            <div
              key={idx}
              className={`h-1.5 rounded-full shadow-sm transition-all duration-300 ${idx === currentIndex ? 'w-4 bg-white' : 'w-1.5 bg-white/50'
                }`}
            />
          ))}
        </div>
      </div>

      {/* 바디 컨텐츠 */}
      <div className="flex-1">
        {/* 리뷰 평점 및 버튼 섹션 */}
        <div className="px-5 py-5 flex items-center justify-between border-b border-gray-100">
          <div className="flex items-center gap-1.5">
            <Image src="/images/map/reviewStarIcon.png" alt="평점" width={20} height={20} className="w-5 h-5 object-contain" />
            <span className="text-[17px] font-medium text-gray-900">{cafe.rating}</span>
          </div>
          <button className="flex items-center text-gray-900 text-[15px] font-medium hover:text-gray-600 transition-colors">
            Review {cafe.reviewCount} <span className="ml-1.5 text-gray-400 font-light">&gt;</span>
          </button>
        </div>

        {/* 기본 정보 섹션 */}
        <div className="px-5 py-6 border-b border-gray-100 border-b-[8px]">
          <h2 className="text-[16px] font-bold text-gray-900 mb-4">기본 정보</h2>
          <div className="space-y-3.5">
            <div className="flex items-center gap-2.5">
              <Image src="/images/map/clockIcon.png" alt="영업시간" width={20} height={20} className="w-5 h-5 object-contain" />
              <span className="text-gray-900 text-[14px] font-medium">{cafe.businessHours}</span>
            </div>
            <div className="flex items-center gap-2.5">
              <Image src="/images/map/locationIcon.png" alt="주소" width={20} height={20} className="w-5 h-5 object-contain" />
              <span className="text-gray-900 text-[14px] font-medium">{cafe.address}</span>
            </div>
            <div className="flex items-center gap-2.5">
              <Image src="/images/map/phoneIcon.png" alt="전화번호" width={20} height={20} className="w-5 h-5 object-contain" />
              <span className="text-gray-900 text-[14px] font-medium">{cafe.phone}</span>
            </div>
          </div>
        </div>

        {/* 메뉴 섹션 */}
        <div className="px-5 py-6">
          <h2 className="text-[16px] font-bold text-gray-900 mb-5">메뉴</h2>
          <div className="space-y-5">
            {/* 메뉴 데이터가 있을 때만 map을 돌리고, 없으면 안내 문구를 보여줍니다. */}
            {cafe.menuList && cafe.menuList.length > 0 ? (
              cafe.menuList.map((menu, idx) => (
                <div key={idx} className="flex gap-4 cursor-pointer hover:bg-gray-50/50 p-1 -m-1 rounded-xl transition-colors">
                  <div className="w-24 h-24 relative shrink-0">
                    <Image
                      src={menu.imageUrl}
                      alt={menu.name}
                      fill
                      className="object-cover rounded-xl"
                    />
                  </div>
                  <div className="flex flex-col justify-center">
                    <h3 className="text-[16px] font-bold text-gray-900 mb-1.5">{menu.name}</h3>
                    <p className="text-[15px] font-medium text-gray-900">{menu.price}</p>
                  </div>
                </div>
              ))
            ) : (
              // 데이터가 없을 때 표시될 UI
              <div className="py-12 flex flex-col items-center justify-center bg-gray-50 rounded-2xl border border-dashed border-gray-200">
                <p className="text-[14px] text-gray-500 font-medium">
                  현재 메뉴 정보 수집 중입니다.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

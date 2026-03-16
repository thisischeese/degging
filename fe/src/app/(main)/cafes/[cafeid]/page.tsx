'use client';

import React, { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { motion } from 'framer-motion';

interface CafeDetail {
  id: string;
  name: string;
  description: string;
  rating: number;
  reviewCount: number;
  businessHours: string;
  address: string;
  phone: string;
  imageUrl: string;
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
        imageUrl: "/images/cafe/cafe1.png",
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
      {/* 상단 비주얼 영역 */}
      <div className="relative w-full h-[360px] shrink-0">
        <Image
          src={cafe.imageUrl}
          alt={cafe.name}
          fill
          className="object-cover"
          priority
        />
        {/* 뒤로가기 버튼 */}
        <button
          onClick={() => router.back()}
          className="absolute top-4 left-4 z-10 w-10 h-10 flex items-center justify-center cursor-pointer hover:opacity-80 transition-opacity"
        >
          <Image src="/images/map/backIcon.png" alt="뒤로가기" width={40} height={40} className="w-10 h-10 object-contain drop-shadow-md" />
        </button>

        {/* 스크랩(별) 버튼 */}
        <button
          className="absolute top-4 right-4 z-10 w-10 h-10 flex items-center justify-center cursor-pointer hover:opacity-80 transition-opacity"
        >
          <Image src="/images/map/unscrappedIcon.png" alt="스크랩" width={40} height={40} className="w-10 h-10 object-contain drop-shadow-md" />
        </button>

        {/* 하단 그라데이션 및 정보 오버레이 */}
        <div className="absolute inset-x-0 bottom-0 h-48 bg-gradient-to-t from-black/80 to-transparent flex flex-col justify-end px-5 pb-8 text-white">
          <h1 className="text-[24px] font-semibold mb-2">{cafe.name}</h1>
          <p className="text-[14px] text-gray-200 leading-snug w-[90%]">{cafe.description}</p>
        </div>

        {/* 인디케이터 (페이지네이션 도트) - 지정된 디자인 */}
        <div className="absolute bottom-4 inset-x-0 flex justify-center items-center gap-1.5 z-10">
          <div className="w-1.5 h-1.5 rounded-full bg-white shadow-sm"></div>
          <div className="w-1.5 h-1.5 rounded-full bg-white/50 shadow-sm"></div>
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
            {cafe.menuList.map((menu, idx) => (
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
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

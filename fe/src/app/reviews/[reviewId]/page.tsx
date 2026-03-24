'use client';

import React, { use, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Star } from 'lucide-react';
import { CafeCard } from '@/common/components/CafeCard';
import { getReviewDetail } from '@/features/reviews/api/reviewApi';
import {
  ensureReviewDetailImages,
  REVIEW_DETAIL_FALLBACK_IMAGE,
} from '@/features/reviews/lib/reviewDetail';
import { ReviewDetailResponse } from '@/features/reviews/types';

// 리뷰 상세 화면에서 사용할 기본 상태를 정의합니다.
const createInitialReviewDetail = (reviewId: string): ReviewDetailResponse => ({
  reviewId,
  rating: 0,
  content: '',
  createdAt: '',
  updatedAt: '',
  imageUrls: [REVIEW_DETAIL_FALLBACK_IMAGE],
  nickname: '',
  name: '',
  cafeIntro: '',
  address: '',
  roadAddress: '',
});

// 리뷰 작성일을 화면용 문자열로 변환합니다.
const formatDate = (dateString: string) => {
  if (!dateString) {
    return '';
  }

  const date = new Date(dateString);

  if (Number.isNaN(date.getTime())) {
    return '';
  }

  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  let hours = date.getHours();
  const minutes = date.getMinutes().toString().padStart(2, '0');
  const period = hours >= 12 ? '오후' : '오전';

  hours = hours % 12 || 12;

  return `${year}년 ${month}월 ${day}일 ${period} ${hours}시 ${minutes}분`;
};

export default function ReviewDetailPage({
  params,
}: {
  params: Promise<{ reviewId: string }> | { reviewId: string };
}) {
  const router = useRouter();
  const resolvedParams = params instanceof Promise ? use(params) : params;

  // 리뷰 조회 상태를 관리합니다.
  const [reviewData, setReviewData] = useState<ReviewDetailResponse>(() =>
    createInitialReviewDetail(resolvedParams.reviewId)
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // 리뷰 이미지 캐러셀 상태를 관리합니다.
  const [currentIndex, setCurrentIndex] = useState(0);
  const [direction, setDirection] = useState(0);
  const [currentImageSrc, setCurrentImageSrc] = useState(REVIEW_DETAIL_FALLBACK_IMAGE);

  // 서버에서 리뷰 상세 데이터를 조회합니다.
  useEffect(() => {
    let isMounted = true;

    const fetchReviewDetail = async () => {
      setLoading(true);
      setError('');

      try {
        const response = await getReviewDetail(resolvedParams.reviewId);

        if (!isMounted) {
          return;
        }

        setReviewData({
          ...response,
          imageUrls: ensureReviewDetailImages(response.imageUrls),
        });
      } catch (fetchError) {
        console.error('Failed to fetch review detail:', fetchError);

        if (!isMounted) {
          return;
        }

        setError('리뷰를 불러오지 못했습니다.');
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchReviewDetail();

    return () => {
      isMounted = false;
    };
  }, [resolvedParams.reviewId]);

  // 리뷰 데이터가 바뀌면 캐러셀 상태를 초기화합니다.
  useEffect(() => {
    const nextImages = ensureReviewDetailImages(reviewData.imageUrls);

    setCurrentIndex(0);
    setDirection(0);
    setCurrentImageSrc(nextImages[0]);
  }, [reviewData.imageUrls]);

  // 현재 캐러셀 인덱스에 맞는 이미지를 반영합니다.
  useEffect(() => {
    const nextImages = ensureReviewDetailImages(reviewData.imageUrls);
    setCurrentImageSrc(nextImages[currentIndex] ?? REVIEW_DETAIL_FALLBACK_IMAGE);
  }, [currentIndex, reviewData.imageUrls]);

  // 카페 카드에 필요한 데이터를 매핑합니다.
  const cafeData = {
    id: '',
    name: reviewData.name || '카페 정보 없음',
    description: reviewData.cafeIntro || '카페 소개가 없습니다.',
    address: reviewData.roadAddress || reviewData.address || '주소 정보 없음',
    imageUrl: ensureReviewDetailImages(reviewData.imageUrls)[0],
  };

  // 캐러셀 스와이프 종료 시 다음 이미지를 계산합니다.
  const handleDragEnd = (offsetX: number, velocityX: number) => {
    const imageUrls = ensureReviewDetailImages(reviewData.imageUrls);

    if (imageUrls.length <= 1) {
      return;
    }

    if (offsetX < -50 || velocityX < -500) {
      setDirection(1);
      setCurrentIndex((previous) => (previous + 1) % imageUrls.length);
      return;
    }

    if (offsetX > 50 || velocityX > 500) {
      setDirection(-1);
      setCurrentIndex((previous) => (previous - 1 + imageUrls.length) % imageUrls.length);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[100dvh] w-full items-center justify-center bg-white font-pretendard text-[15px] text-gray-500">
        리뷰를 불러오는 중입니다...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[100dvh] w-full flex-col items-center justify-center gap-4 bg-white px-6 text-center font-pretendard">
        <p className="text-[15px] text-gray-700">{error}</p>
        <button
          onClick={() => router.back()}
          className="rounded-full border border-gray-900 px-4 py-2 text-[14px] font-medium text-gray-900 transition-colors hover:bg-gray-100"
        >
          이전 화면으로
        </button>
      </div>
    );
  }

  const imageUrls = ensureReviewDetailImages(reviewData.imageUrls);

  return (
    <div className="flex min-h-[100dvh] w-full flex-col bg-[#FFFFFF] font-pretendard">
      {/* 리뷰 상세 상단 헤더를 표시합니다. */}
      <header className="sticky top-0 z-10 border-b border-gray-200 bg-[#F9F9F4]">
        <div className="flex h-14 items-center justify-between px-4 pt-safe-top">
          <button
            onClick={() => router.back()}
            className="flex h-10 w-10 items-center justify-center rounded-full border border-gray-900 bg-transparent transition-colors hover:bg-gray-100"
          >
            <ArrowLeft className="h-5 w-5 text-gray-900" strokeWidth={1.2} />
          </button>
          <h1 className="absolute left-1/2 -translate-x-1/2 text-[16px] font-bold text-gray-900">
            리뷰 상세
          </h1>
          <div className="h-10 w-10" />
        </div>
      </header>

      {/* 리뷰 상세 본문 콘텐츠를 표시합니다. */}
      <main className="relative flex-1 overflow-y-auto no-scrollbar">
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className="mx-auto flex w-full max-w-md flex-col pb-8"
        >
          {/* 리뷰에 연결된 카페 정보를 표시합니다. */}
          {/* pointer-events-none을 추가하여 클릭이 안 되는 순수 정보 카드로 지정함. */}
          <div className="px-5 pb-4 pt-5">
            <div className="overflow-hidden rounded-2xl shadow-sm pointer-events-none">
              <CafeCard
                id={cafeData.id}
                name={cafeData.name}
                description={cafeData.description}
                address={cafeData.address}
                imageUrl={cafeData.imageUrl}
              />
            </div>
          </div>

          {/* 리뷰 이미지 캐러셀을 표시합니다. */}
          <div className="relative w-full shrink-0 px-5">
            <div className="relative aspect-square w-full overflow-hidden rounded-2xl bg-gray-100 shadow-sm touch-pan-y">
              <AnimatePresence initial={false} custom={direction}>
                <motion.div
                  key={currentIndex}
                  custom={direction}
                  variants={{
                    enter: (currentDirection: number) => ({
                      x: currentDirection > 0 ? 100 : -100,
                      opacity: 0,
                      zIndex: 1,
                    }),
                    center: {
                      zIndex: 1,
                      x: 0,
                      opacity: 1,
                    },
                    exit: (currentDirection: number) => ({
                      zIndex: 0,
                      x: currentDirection > 0 ? -50 : 50,
                      opacity: 0,
                    }),
                  }}
                  initial="enter"
                  animate="center"
                  exit="exit"
                  transition={{
                    x: { type: 'spring', stiffness: 300, damping: 30 },
                    opacity: { duration: 0.3 },
                  }}
                  className="absolute inset-0 h-full w-full cursor-grab active:cursor-grabbing"
                  drag="x"
                  dragConstraints={{ left: 0, right: 0 }}
                  dragElastic={0.2}
                  onDragEnd={(_, info) => handleDragEnd(info.offset.x, info.velocity.x)}
                >
                  <Image
                    src={currentImageSrc}
                    alt={`리뷰 상세 이미지 ${currentIndex + 1}`}
                    fill
                    className="pointer-events-none object-cover"
                    draggable={false}
                    priority={currentIndex === 0}
                    unoptimized
                    onError={() => setCurrentImageSrc(REVIEW_DETAIL_FALLBACK_IMAGE)}
                  />
                </motion.div>
              </AnimatePresence>

              {imageUrls.length > 1 ? (
                <div className="pointer-events-none absolute inset-x-0 bottom-4 z-20 flex items-center justify-center gap-1.5">
                  {imageUrls.map((_, index) => (
                    <div
                      key={`${reviewData.reviewId}-${index}`}
                      className={`h-1.5 rounded-full shadow-sm transition-all duration-300 ${index === currentIndex ? 'w-4 bg-white opacity-100' : 'w-1.5 bg-white opacity-50'
                        }`}
                    />
                  ))}
                </div>
              ) : null}
            </div>
          </div>

          {/* 리뷰 작성자와 별점을 표시합니다. */}
          <div className="mb-3 mt-4 flex items-center justify-between px-5">
            <div className="flex flex-col justify-center">
              <span className="mb-0.5 text-[15px] font-bold text-gray-900">
                @{reviewData.nickname || '알 수 없음'}
              </span>
              <span className="text-[13px] font-medium text-gray-500">{formatDate(reviewData.createdAt)}</span>
            </div>
            <div className="mt-1 flex shrink-0 items-center gap-1.5 self-start">
              <Star className="h-[22px] w-[22px] fill-[#FFC107] text-[#FFC107]" />
              <span className="mt-0.5 text-[17px] font-bold leading-none text-gray-900">
                {reviewData.rating}
              </span>
            </div>
          </div>

          {/* 리뷰 본문 내용을 표시합니다. */}
          <div className="px-5">
            <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
              <p className="whitespace-pre-line break-all text-[15px] font-medium leading-relaxed text-gray-900">
                {reviewData.content}
              </p>
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  );
}

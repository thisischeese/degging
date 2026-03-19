'use client';

import React, { use, useEffect, useRef, useState } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { motion } from 'framer-motion';
import { ArrowLeft, Pencil, Star } from 'lucide-react';
import PopUp from '@/common/components/PopUp';
import { getCafeReviews } from '@/features/reviews/api/reviewApi';
import { CafeReviewResponse, StoredCafeReview } from '@/features/reviews/types';

const PAGE_SIZE = 10;
const FALLBACK_IMAGE = '/images/cafe/baseCafeImage.png';

const mapStoredReviewToCafeReview = (review: StoredCafeReview): CafeReviewResponse => ({
  reviewId: review.id,
  rating: review.rating,
  content: review.content,
  createdAt: new Date(review.timestamp).toISOString(),
  updatedAt: new Date(review.timestamp).toISOString(),
  images: review.imageUrl
    ? [{ imageId: `local-${review.id}`, imageUrl: review.imageUrl }]
    : [],
  nickname: '나',
});

const mergeReviews = (
  localReviews: CafeReviewResponse[],
  remoteReviews: CafeReviewResponse[]
): CafeReviewResponse[] => {
  const merged: CafeReviewResponse[] = [];
  const seen = new Set<string>();

  [...localReviews, ...remoteReviews].forEach((review) => {
    if (seen.has(review.reviewId)) return;
    seen.add(review.reviewId);
    merged.push(review);
  });

  return merged;
};

const formatReviewDate = (dateString: string) => {
  const date = new Date(dateString);

  if (Number.isNaN(date.getTime())) {
    return '';
  }

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  return `${year}.${month}.${day}`;
};

export default function CafeReviewsPage({ params }: { params: Promise<{ cafeid: string }> | { cafeid: string } }) {
  const router = useRouter();
  const resolvedParams = params instanceof Promise ? use(params) : params;
  const cafeId = resolvedParams.cafeid;

  const [showPopup, setShowPopup] = useState(false);
  const [localReviews, setLocalReviews] = useState<CafeReviewResponse[]>([]);
  const loadMoreRef = useRef<HTMLDivElement | null>(null);

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isError,
    isFetching,
    isFetchingNextPage,
    isLoading,
    refetch,
  } = useInfiniteQuery({
    queryKey: ['cafeReviews', cafeId],
    queryFn: ({ pageParam }) => getCafeReviews(cafeId, pageParam, PAGE_SIZE),
    initialPageParam: 0,
    getNextPageParam: (lastPage) => (lastPage.last ? undefined : lastPage.number + 1),
    enabled: Boolean(cafeId),
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const timer = window.setTimeout(() => {
      try {
        const localReviewsStr = localStorage.getItem(`cafeReviews-${cafeId}`);
        const parsedReviews: StoredCafeReview[] = localReviewsStr ? JSON.parse(localReviewsStr) : [];
        const mappedReviews = parsedReviews
          .map(mapStoredReviewToCafeReview)
          .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

        setLocalReviews(mappedReviews);
      } catch (parseError) {
        console.error('Failed to parse local cafe reviews:', parseError);
        setLocalReviews([]);
      }

      if (sessionStorage.getItem('reviewSuccess') === 'true') {
        setShowPopup(true);
        sessionStorage.removeItem('reviewSuccess');
      }
    }, 0);

    return () => window.clearTimeout(timer);
  }, [cafeId]);

  useEffect(() => {
    if (!loadMoreRef.current || !hasNextPage || isFetchingNextPage) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry?.isIntersecting) {
          fetchNextPage();
        }
      },
      { rootMargin: '160px' }
    );

    observer.observe(loadMoreRef.current);

    return () => observer.disconnect();
  }, [fetchNextPage, hasNextPage, isFetchingNextPage, data]);

  const pages = data?.pages ?? [];
  const reviews =
    pages.length > 0
      ? pages.flatMap((page, index) =>
          index === 0 ? mergeReviews(localReviews, page.content) : page.content
        )
      : localReviews;

  const showInitialError = isError && pages.length === 0 && localReviews.length === 0;
  const showInlineError = isError && localReviews.length > 0;

  return (
    <div className="w-full min-h-[100dvh] bg-[#FFFFFF] font-pretendard flex flex-col relative">
      <PopUp
        message="리뷰 작성이 완료되었습니다."
        isVisible={showPopup}
        onClose={() => setShowPopup(false)}
      />

      <header className="sticky top-0 z-10 bg-[#F9F9F4] border-b border-gray-200">
        <div className="flex items-center justify-between h-14 px-4 pt-safe-top">
          <button
            onClick={() => router.back()}
            className="w-10 h-10 flex items-center justify-center rounded-full border border-gray-900 bg-transparent hover:bg-gray-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-900" strokeWidth={1.2} />
          </button>
          <h1 className="text-[16px] font-bold text-gray-900">카페 리뷰</h1>
          <button
            onClick={() => router.push(`/cafes/${cafeId}/reviews/new`)}
            className="w-10 h-10 flex items-center justify-center rounded-full border border-gray-900 bg-transparent hover:bg-gray-100 transition-colors"
          >
            <Pencil className="w-5 h-5 text-gray-900" strokeWidth={1.2} />
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-5 py-6 flex flex-col items-center w-full no-scrollbar">
        {showInitialError ? (
          <div className="w-full max-w-md flex-1 flex flex-col items-center justify-center gap-4 text-center">
            <p className="text-[15px] text-gray-700">리뷰를 불러오지 못했습니다.</p>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 rounded-full border border-gray-900 text-[14px] font-medium text-gray-900 hover:bg-gray-100 transition-colors"
            >
              다시 시도
            </button>
          </div>
        ) : isLoading && localReviews.length === 0 ? (
          <div className="w-full max-w-md flex-1 flex items-center justify-center text-[15px] text-gray-500">
            리뷰를 불러오는 중...
          </div>
        ) : reviews.length === 0 ? (
          <div className="w-full max-w-md flex-1 flex items-center justify-center text-[15px] text-gray-500">
            아직 등록된 리뷰가 없습니다.
          </div>
        ) : (
          <motion.div
            initial={{ y: 10, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
            className="space-y-6 w-full max-w-md"
          >
            {showInlineError ? (
              <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-[13px] text-red-700">
                서버 리뷰를 불러오지 못해 임시 저장된 리뷰만 보여주고 있습니다.
              </div>
            ) : null}

            {reviews.map((review, index) => {
              const imageUrl = review.images[0]?.imageUrl || FALLBACK_IMAGE;

              return (
                <div
                  key={review.reviewId}
                  onClick={() => router.push(`/reviews/${review.reviewId}`)}
                  className="bg-white rounded-xl shadow-md border border-gray-100 flex flex-col overflow-hidden cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all duration-200"
                >
                  <div className="relative w-full h-40 bg-gray-100">
                    <Image
                      src={imageUrl}
                      alt={`리뷰 이미지 ${review.reviewId}`}
                      fill
                      className="object-cover"
                      priority={index === 0}
                    />
                  </div>

                  <div className="p-4 flex flex-col gap-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-[14px] font-semibold text-gray-900 truncate">{review.nickname}</p>
                        <p className="text-[12px] text-gray-400">{formatReviewDate(review.createdAt)}</p>
                      </div>
                      <div className="flex items-center gap-1.5 shrink-0">
                        <Star className="w-5 h-5 text-[#FFD700] fill-[#FFD700]" />
                        <span className="text-[14px] font-medium text-gray-900">{review.rating}</span>
                      </div>
                    </div>

                    <p className="text-[14px] text-gray-900 leading-relaxed break-all line-clamp-3">
                      {review.content}
                    </p>
                  </div>
                </div>
              );
            })}

            {hasNextPage ? <div ref={loadMoreRef} className="h-8 w-full" /> : null}

            {isFetchingNextPage ? (
              <p className="text-center text-[14px] text-gray-500">리뷰를 더 불러오는 중...</p>
            ) : null}

            {isFetching && !isFetchingNextPage && pages.length > 0 ? (
              <p className="text-center text-[13px] text-gray-400">최신 리뷰를 확인하는 중...</p>
            ) : null}
          </motion.div>
        )}
      </main>
    </div>
  );
}

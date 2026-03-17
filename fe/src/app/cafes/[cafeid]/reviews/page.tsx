'use client';

import React, { use, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { motion } from 'framer-motion';
import { ArrowLeft, Pencil, Star } from 'lucide-react';
import PopUp from '@/common/components/PopUp';

interface Review {
  id: string;
  rating: number;
  content: string;
  imageUrl: string;
}

const mockReviews: Review[] = [
  {
    id: '1',
    rating: 3.5,
    content: '카페 공간이 넓고 샌드위치 맛있었어요! 감사합니다',
    imageUrl: '/images/cafe/cafe1.png',
  },
  {
    id: '2',
    rating: 3.5,
    content: '카페 공간이 넓고 샌드위치 맛있었어요! 감사합니다',
    imageUrl: '/images/cafe/cafe2.png',
  },
  {
    id: '3',
    rating: 3.5,
    content: '카페 공간이 넓고 샌드위치 맛있었어요! 감사합니다',
    imageUrl: '/images/cafe/cafe1.png',
  },
];

export default function CafeReviewsPage({ params }: { params: Promise<{ cafeid: string }> | { cafeid: string } }) {
  const router = useRouter();

  // React 18/19 compatibility for params
  const resolvedParams = params instanceof Promise ? use(params) : params;

  const [reviews, setReviews] = useState<Review[]>(mockReviews);
  const [showPopup, setShowPopup] = useState(false);

  useEffect(() => {
    // Load local reviews from LocalStorage asynchronously to avoid cascading renders
    const timer = setTimeout(() => {
        const localReviewsStr = localStorage.getItem(`cafeReviews-${resolvedParams.cafeid}`);
        if (localReviewsStr) {
            try {
                const localReviews = JSON.parse(localReviewsStr);
                setReviews([...localReviews, ...mockReviews]);
            } catch(e) {
                console.error('Failed to parse local reviews', e);
            }
        }
    }, 0);

    // Check if we just submitted a review asynchronously to avoid cascading renders
    const popupTimer = setTimeout(() => {
        if (sessionStorage.getItem('reviewSuccess') === 'true') {
            setShowPopup(true);
            sessionStorage.removeItem('reviewSuccess');
        }
    }, 0);

    return () => {
        clearTimeout(timer);
        clearTimeout(popupTimer);
    };
  }, [resolvedParams.cafeid]);

  return (
    <div className="w-full min-h-[100dvh] bg-[#FFFFFF] font-pretendard flex flex-col relative">
      <PopUp 
        message="리뷰 작성이 완료되었습니다." 
        isVisible={showPopup} 
        onClose={() => setShowPopup(false)} 
      />
      {/* 헤더 섹션 */}
      <header className="sticky top-0 z-10 bg-[#F9F9F4] border-b border-gray-200">
        <div className="flex items-center justify-between h-14 px-4 pt-safe-top">
          <button
            onClick={() => router.back()}
            className="w-10 h-10 flex items-center justify-center rounded-full border border-gray-900 bg-transparent hover:bg-gray-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-900" strokeWidth={1.2} />
          </button>
          <h1 className="text-[16px] font-bold text-gray-900">아우어베이커리 역삼점</h1>
          <button
            onClick={() => router.push(`/cafes/${resolvedParams.cafeid}/reviews/new`)}
            className="w-10 h-10 flex items-center justify-center rounded-full border border-gray-900 bg-transparent hover:bg-gray-100 transition-colors"
          >
            <Pencil className="w-5 h-5 text-gray-900" strokeWidth={1.2} />
          </button>
        </div>
      </header>

      {/* 바디 섹션 - 리뷰 카드 리스트 */}
      <main className="flex-1 overflow-y-auto px-5 py-6 flex flex-col items-center w-full no-scrollbar">
        <motion.div
          initial={{ y: 10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
          className="space-y-6 w-full max-w-md"
        >
          {reviews.map((review) => (
            <div
              key={review.id}
              onClick={() => router.push(`/reviews/${review.id}`)}
              className="bg-white rounded-xl shadow-md border border-gray-100 flex flex-col overflow-hidden cursor-pointer hover:shadow-lg hover:scale-[1.02] transition-all duration-200"
            >
              <div className="relative w-full h-40 bg-gray-100">
                <Image
                  src={review.imageUrl}
                  alt={`리뷰 이미지 ${review.id}`}
                  fill
                  className="object-cover"
                  priority={review.id === '1'}
                />
              </div>
              <div className="p-4 flex flex-col gap-2.5">
                <div className="flex items-center gap-1.5">
                  <Star className="w-5 h-5 text-[#FFD700] fill-[#FFD700]" />
                  <span className="text-[14px] font-medium text-gray-900">{review.rating}</span>
                </div>
                <p className="text-[14px] text-gray-900 leading-relaxed break-all line-clamp-2">
                  {review.content}
                </p>
              </div>
            </div>
          ))}
        </motion.div>
      </main>
    </div>
  );
}

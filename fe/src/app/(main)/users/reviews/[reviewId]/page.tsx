'use client';

import React, { use, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, MoreVertical, Star } from 'lucide-react';
import { CafeCard } from '@/common/components/CafeCard';
import { Dropdown } from '@/common/components/Dropdown';

// 인터페이스 (기존 코드 참고 및 types.ts 호환)
interface LocalReview {
  id: string;
  rating: number;
  content: string;
  imageUrl: string;
  timestamp: number;
}

interface ReviewDetail {
  reviewId: string;
  rating: number;
  content: string;
  createdAt: string;
  imageUrls: string[];
  nickname: string;
  name: string;       // 카페 이름
  cafeIntro: string;  // 카페 설명
  roadAddress: string;// 카페 주소
}

export default function MyReviewDetailPage({ params }: { params: Promise<{ reviewId: string }> | { reviewId: string } }) {
  const router = useRouter();
  const resolvedParams = params instanceof Promise ? use(params) : params;

  const mockReviewDetail: ReviewDetail = {
    reviewId: resolvedParams.reviewId,
    rating: 3.5,
    content: "유명하다해서 기대하며 방문했는데 생각보다 응대가 친절하지 않았어요. ....... ㅜㅜ\n\n그래도 익숙하면서도 새로운 식감의 맛, 특히 시그니처 메뉴인 더티초코가 먹기는 힘들었지만 정말 맛있었어요. 그리고 공간이 넓어서 모임하기 좋았어요.",
    createdAt: "2026-02-25T14:52:00Z",
    imageUrls: ["/images/cafe/cafe1.png", "/images/cafe/cafe2.png"],
    nickname: "SAYCH22Z",
    name: "아우어베이커리 역삼점",
    cafeIntro: "조용하고 넓은 공간에서 즐기는 시그니처 빵",
    roadAddress: "서울 강남구 언주로85길 29 1층"
  };

  const [reviewData, setReviewData] = useState<ReviewDetail>(mockReviewDetail);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [direction, setDirection] = useState(0);

  useEffect(() => {
    // localStorage에서 리뷰 찾기 로직
    const loadLocalData = () => {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('cafeReviews-')) {
          try {
            const localReviews: LocalReview[] = JSON.parse(localStorage.getItem(key) || '[]');
            const foundReview = localReviews.find((r) => r.id === resolvedParams.reviewId);

            if (foundReview) {
              // [오류 해결] setTimeout을 사용하여 다음 틱(Task)에서 업데이트되도록 합니다.
              // 이렇게 하여 "동기적 호출(Synchronous)" 경고 해결
              setTimeout(() => {
                setReviewData(prev => ({
                  ...prev,
                  reviewId: foundReview.id,
                  rating: foundReview.rating,
                  content: foundReview.content,
                  imageUrls: [foundReview.imageUrl],
                  createdAt: foundReview.timestamp
                    ? new Date(foundReview.timestamp).toISOString()
                    : new Date().toISOString()
                }));
              }, 0);
              break;
            }
          } catch (e) {
            console.error(e);
          }
        }
      }
    };

    loadLocalData();
  }, [resolvedParams.reviewId]);

  const formatDate = (dateString: string) => {
    const d = new Date(dateString);
    const year = d.getFullYear();
    const month = d.getMonth() + 1;
    const day = d.getDate();

    let hours = d.getHours();
    const minutes = d.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? '오후' : '오전';

    hours = hours % 12;
    hours = hours ? hours : 12;

    return `${year}년 ${month}월 ${day}일 ${ampm} ${hours}시 ${minutes}분`;
  };

  const cafeData = {
    id: "cafe-id-placeholder",
    name: reviewData.name,
    description: reviewData.cafeIntro,
    address: reviewData.roadAddress,
    imageUrl: reviewData.imageUrls[0] || '/images/cafe/baseCafeImage.png',
  };

  const handleDropdown = (val: string) => {
    if (val === 'edit') {
      router.push(`/users/reviews/${resolvedParams.reviewId}/edit`);
    } else if (val === 'delete') {
      if (window.confirm('리뷰를 삭제하시겠습니까?')) {
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (key && key.startsWith('cafeReviews-')) {
            try {
              const localReviews: LocalReview[] = JSON.parse(localStorage.getItem(key) || '[]');
              const filtered = localReviews.filter((r) => r.id !== resolvedParams.reviewId);
              if (filtered.length !== localReviews.length) {
                localStorage.setItem(key, JSON.stringify(filtered));
                break;
              }
            } catch { }
          }
        }
        // 수정된 사항 반영을 위해 목록으로 이동 후 새로고침 (문제 구체적인 로직 반영)
        router.replace('/users/reviews');
        setTimeout(() => {
          window.location.reload();
        }, 50);
      }
    }
  };

  return (
    <div className="w-full min-h-[100dvh] bg-[#FFFFFF] font-pretendard flex flex-col max-w-md mx-auto relative">
      <header className="sticky top-0 z-10 bg-[#F9F9F4] border-b border-gray-200">
        <div className="flex items-center justify-between h-14 px-4 pt-safe-top">
          <button
            onClick={() => router.back()}
            className="w-10 h-10 flex items-center justify-center rounded-full border border-gray-900 bg-transparent hover:bg-gray-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-900" strokeWidth={1.2} />
          </button>
          <h1 className="text-[16px] font-bold text-gray-900 absolute left-1/2 -translate-x-1/2">
            마이 리뷰
          </h1>
          <div className="relative flex items-center justify-center w-10 h-10">
            <Dropdown
              options={[
                { label: '수정', value: 'edit' },
                { label: '삭제', value: 'delete' }
              ]}
              value=""
              onChange={handleDropdown}
              triggerNode={
                <button className="flex items-center justify-center w-10 h-10 rounded-full bg-transparent hover:bg-gray-100 transition-colors pointer-events-auto">
                  <MoreVertical className="w-6 h-6 text-gray-900" strokeWidth={1.5} />
                </button>
              }
            />
          </div>
        </div>
      </header>

      <main className="flex-1 w-full overflow-y-auto relative no-scrollbar pb-20">
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className="flex flex-col pb-8 mx-auto w-full"
        >
          <div className="px-5 pt-5 pb-4">
            <div className="shadow-sm rounded-2xl overflow-hidden">
              <CafeCard
                id={cafeData.id}
                name={cafeData.name}
                description={cafeData.description}
                address={cafeData.address}
                imageUrl={cafeData.imageUrl}
              />
            </div>
          </div>

          <div className="px-5 relative w-full shrink-0">
            <div className="w-full relative rounded-2xl overflow-hidden shadow-sm aspect-square bg-gray-100 touch-pan-y">
              <AnimatePresence initial={false} custom={direction}>
                <motion.div
                  key={currentIndex}
                  custom={direction}
                  variants={{
                    enter: (dir: number) => ({
                      x: dir > 0 ? 100 : -100,
                      opacity: 0,
                      zIndex: 1,
                    }),
                    center: {
                      zIndex: 1,
                      x: 0,
                      opacity: 1,
                    },
                    exit: (dir: number) => ({
                      zIndex: 0,
                      x: dir > 0 ? -50 : 50,
                      opacity: 0,
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
                    if (swipe < -50 || velocity.x < -500) {
                      setDirection(1);
                      setCurrentIndex((prev) => (prev + 1) % reviewData.imageUrls.length);
                    } else if (swipe > 50 || velocity.x > 500) {
                      setDirection(-1);
                      setCurrentIndex((prev) => (prev - 1 + reviewData.imageUrls.length) % reviewData.imageUrls.length);
                    }
                  }}
                >
                  <Image
                    src={reviewData.imageUrls[currentIndex]}
                    alt={`리뷰 상세 이미지 ${currentIndex + 1}`}
                    fill
                    className="object-cover pointer-events-none"
                    draggable={false}
                    priority={currentIndex === 0}
                    unoptimized
                  />
                </motion.div>
              </AnimatePresence>

              {reviewData.imageUrls.length > 1 && (
                <div className="absolute bottom-4 inset-x-0 flex justify-center items-center gap-1.5 z-20 pointer-events-none">
                  {reviewData.imageUrls.map((_, i) => (
                    <div
                      key={i}
                      className={`h-1.5 rounded-full shadow-sm transition-all duration-300 ${i === currentIndex ? 'w-4 bg-white opacity-100' : 'w-1.5 bg-white opacity-50'}`}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="px-5 flex items-center justify-between mt-4 mb-3">
            <div className="flex flex-col justify-center">
              <span className="text-[15px] font-bold text-gray-900 mb-0.5">
                @{reviewData.nickname}
              </span>
              <span className="text-[13px] text-gray-500 font-medium">
                {formatDate(reviewData.createdAt)}
              </span>
            </div>
            <div className="flex items-center gap-1.5 shrink-0 self-start mt-1">
              <Star className="w-[22px] h-[22px] text-[#FFC107] fill-[#FFC107]" />
              <span className="text-[17px] font-bold text-gray-900 leading-none mt-0.5">
                {reviewData.rating}
              </span>
            </div>
          </div>

          <div className="px-5">
            <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
              <p className="text-[15px] text-gray-900 leading-relaxed whitespace-pre-line break-words break-all font-medium">
                {reviewData.content}
              </p>
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  );
}

'use client';

import React, { use } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Star } from 'lucide-react';
import { CafeCard } from '@/common/components/CafeCard';

// API 명세 기반 리뷰 데이터 인터페이스
interface ReviewDetail {
  reviewId: string;
  rating: number;
  content: string;
  createdAt: string; // API에 따라 ISO 8601 문자열 또는 미리 포맷된 형태
  imageUrls: string[];
  nickname: string;
  name: string;       // 카페 이름
  cafeIntro: string;  // 카페 설명
  roadAddress: string;// 카페 주소
}

interface LocalReview {
  id: string;
  rating: number;
  content: string;
  imageUrl: string;
  timestamp: number;
}

export default function ReviewDetailPage({ params }: { params: Promise<{ reviewId: string }> | { reviewId: string } }) {
  const router = useRouter();
  const resolvedParams = params instanceof Promise ? use(params) : params;
  
  // 목업 데이터 (API 응답 구조와 동일하게 설정)
  const mockReviewDetail: ReviewDetail = {
    reviewId: resolvedParams.reviewId,
    rating: 3.5,
    content: "유명하다해서 기대하며 방문했는데 생각보다 응대가 친절하지 않았어요. ....... ㅜㅜ\n\n그래도 익숙하면서도 새로운 식감의 맛, 특히 시그니처 메뉴인 더티초코가 먹기는 힘들었지만 정말 맛있었어요. 그리고 공간이 넓어서 모임하기 좋았어요.",
    createdAt: "2026-02-25T14:52:00Z", // 원본 데이터. 포맷팅은 리액트 내에서 처리함.
    imageUrls: ["/images/cafe/cafe1.png", "/images/cafe/cafe2.png"],
    nickname: "SAYCH22Z",
    name: "아우어베이커리 역삼점",
    cafeIntro: "조용하고 넓은 공간에서 즐기는 시그니처 빵",
    roadAddress: "서울 강남구 언주로85길 29 1층"
  };

  const [reviewData, setReviewData] = React.useState<ReviewDetail>(mockReviewDetail);

  React.useEffect(() => {
    // 로컬에서 생성된 리뷰인 경우 localStorage에서 찾기
    if (resolvedParams.reviewId.startsWith('local-')) {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('cafeReviews-')) {
          try {
            const localReviews: LocalReview[] = JSON.parse(localStorage.getItem(key) || '[]');
            const foundReview = localReviews.find((r) => r.id === resolvedParams.reviewId);
            if (foundReview) {
              setReviewData(prev => ({
                ...prev,
                reviewId: foundReview.id,
                rating: foundReview.rating,
                content: foundReview.content,
                imageUrls: [foundReview.imageUrl],
                createdAt: foundReview.timestamp ? new Date(foundReview.timestamp).toISOString() : new Date().toISOString()
              }));
              break;
            }
          } catch(e) {
            console.error(e);
          }
        }
      }
    } else {
        // 목업 ID별로 기본적인 목업 리뷰 차이 처리
        if (resolvedParams.reviewId === '2') {
            setReviewData(prev => ({...prev, imageUrls: ['/images/cafe/cafe2.png']}));
        } else if (resolvedParams.reviewId === '3') {
            setReviewData(prev => ({...prev, imageUrls: ['/images/cafe/cafe1.png']}));
        }
    }
  }, [resolvedParams.reviewId]);

  // 날짜 포맷팅 함수 (예: 2026년 2월 25일 오후 2시 52분)
  const formatDate = (dateString: string) => {
    const d = new Date(dateString);
    const year = d.getFullYear();
    const month = d.getMonth() + 1;
    const day = d.getDate();
    
    let hours = d.getHours();
    const minutes = d.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? '오후' : '오전';
    
    hours = hours % 12;
    hours = hours ? hours : 12; // 0시는 12시로 표기
    
    return `${year}년 ${month}월 ${day}일 ${ampm} ${hours}시 ${minutes}분`;
  };

  // CafeCard에 넘길 데이터 매핑
  const cafeData = {
    id: "cafe-id-placeholder", // API Spec에 cafeId가 필요하다면 추가, 여기선 placeholder
    name: reviewData.name,
    description: reviewData.cafeIntro,
    address: reviewData.roadAddress,
    imageUrl: mockReviewDetail.imageUrls[0] || '/images/cafe/baseCafeImage.png', // 카페 카드는 리뷰 사진이 아닌 원래 카페 썸네일 사용
  };

  // 슬라이더 상태
  const [currentIndex, setCurrentIndex] = React.useState(0);
  const [direction, setDirection] = React.useState(0);

  return (
    <div className="w-full min-h-[100dvh] bg-[#FFFFFF] font-pretendard flex flex-col">
      {/* 헤더 섹션 */}
      <header className="sticky top-0 z-10 bg-[#F9F9F4] border-b border-gray-200">
        <div className="flex items-center justify-between h-14 px-4 pt-safe-top">
          <button
            onClick={() => router.back()}
            className="w-10 h-10 flex items-center justify-center rounded-full border border-gray-900 bg-transparent hover:bg-gray-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-900" strokeWidth={1.2} />
          </button>
          <h1 className="text-[16px] font-bold text-gray-900 absolute left-1/2 -translate-x-1/2">
            리뷰 상세
          </h1>
          {/* 우측 여백을 맞춰주기 위한 빈 박스 */}
          <div className="w-10 h-10"></div>
        </div>
      </header>

      {/* 바디 섹션 - 스크롤 가능하도록 flex-1 컨테이너에 overflow 추가 */}
      <main className="flex-1 w-full overflow-y-auto relative no-scrollbar">
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className="flex flex-col pb-8 mx-auto max-w-md"
        >
          {/* 최상단 카페 정보 카드 (외곽 여백 필요) */}
          <div className="px-5 pt-5 pb-4">
            <div className="shadow-sm rounded-2xl overflow-hidden">
              <CafeCard
                id={cafeData.id}
                name={cafeData.name}
                description={cafeData.description}
                address={cafeData.address}
                imageUrl={cafeData.imageUrl}
                onClick={() => router.push(`/cafes/${cafeData.id}`)}
              />
            </div>
          </div>

          {/* 메인 이미지 갤러리 - Framer Motion 적용 */}
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
                        // 다음 이미지 (왼쪽으로 스와이프)
                        setDirection(1);
                        setCurrentIndex((prev) => (prev + 1) % reviewData.imageUrls.length);
                      } else if (swipe > 50 || velocity.x > 500) {
                        // 이전 이미지 (오른쪽으로 스와이프)
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
                   />
                 </motion.div>
               </AnimatePresence>

               {/* 페이지네이션 닷 (이미지가 2개 이상일 때만 표시) */}
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

          {/* 작성자 정보 및 별점 */}
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

          {/* 리뷰 내용 박스 */}
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

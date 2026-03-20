import { ReviewDetailResponse, StoredCafeReview } from '@/features/reviews/types';

// 리뷰 상세 화면에서 공통으로 사용하는 기본 이미지 경로입니다.
export const REVIEW_DETAIL_FALLBACK_IMAGE = '/images/cafe/baseCafeImage.png';

// 리뷰 이미지 배열이 비어 있을 때 기본 이미지를 보정합니다.
export const ensureReviewDetailImages = (imageUrls: string[] | undefined): string[] => {
  return imageUrls && imageUrls.length > 0 ? imageUrls : [REVIEW_DETAIL_FALLBACK_IMAGE];
};

// 로컬 저장 리뷰를 상세 조회 응답 형식으로 변환합니다.
export const mapLocalReviewToDetail = (review: StoredCafeReview): ReviewDetailResponse => {
  const createdAt = review.timestamp ? new Date(review.timestamp).toISOString() : new Date().toISOString();

  return {
    reviewId: review.id,
    rating: review.rating,
    content: review.content,
    createdAt,
    updatedAt: createdAt,
    imageUrls: ensureReviewDetailImages(review.imageUrl ? [review.imageUrl] : []),
    nickname: '나',
    name: '내가 작성한 카페 리뷰',
    cafeIntro: '로컬에 저장된 리뷰입니다.',
    address: '주소 정보 없음',
    roadAddress: '주소 정보 없음',
  };
};

// 로컬 저장소에서 리뷰 상세 데이터를 찾습니다.
export const getLocalReviewDetail = (reviewId: string): ReviewDetailResponse | null => {
  if (typeof window === 'undefined') {
    return null;
  }

  for (let index = 0; index < localStorage.length; index += 1) {
    const key = localStorage.key(index);

    if (!key || !key.startsWith('cafeReviews-')) {
      continue;
    }

    try {
      const rawData = localStorage.getItem(key);
      const reviews: StoredCafeReview[] = rawData ? JSON.parse(rawData) : [];
      const matchedReview = reviews.find((review) => review.id === reviewId);

      if (matchedReview) {
        return mapLocalReviewToDetail(matchedReview);
      }
    } catch (error) {
      console.error('Failed to parse local review detail:', error);
    }
  }

  return null;
};

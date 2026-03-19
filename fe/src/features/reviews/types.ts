/**
 * 리뷰 관련 타입 정의
 */

// 1. 리뷰 이미지 인터페이스
export interface ReviewImage {
  imageId: string;
  imageUrl: string;
}

export interface StoredCafeReview {
  id: string;
  rating: number;
  content: string;
  imageUrl: string;
  timestamp: number;
}

// 2. 개별 리뷰 아이템 인터페이스 (API 응답 기준)
export interface Review {
  reviewId: string;
  rating: number;
  content: string;
  createdAt: string;
  updatedAt: string;
  images: ReviewImage[];
  nickname: string;
  cafeName?: string; // 전체 조회에는 없지만 상세 조회나 기존 목업 데이터 호환을 위해 추가 가능
}

// 3. 페이지네이션 정보 인터페이스
export interface Pageable {
  pageNumber: number;
  pageSize: number;
  sort: {
    empty: boolean;
    sorted: boolean;
    unsorted: boolean;
  };
  offset: number;
  unpaged: boolean;
  paged: boolean;
}

// 4. 내 리뷰 전체 조회 응답 인터페이스
export interface MyReviewsResponse {
  content: Review[];
  pageable: Pageable;
  size: number;
  number: number;
  sort: {
    empty: boolean;
    sorted: boolean;
    unsorted: boolean;
  };
  first: boolean;
  last: boolean;
  numberOfElements: number;
  empty: boolean;
}

export interface CafeReviewImageDto {
  imageId: string;
  imageUrl: string;
}

export interface CafeReviewResponse {
  reviewId: string;
  rating: number;
  content: string;
  createdAt: string;
  updatedAt: string;
  images: CafeReviewImageDto[];
  nickname: string;
}

export interface CafeReviewsSliceResponse {
  content: CafeReviewResponse[];
  pageable: Pageable;
  size: number;
  number: number;
  sort: {
    empty: boolean;
    sorted: boolean;
    unsorted: boolean;
  };
  first: boolean;
  last: boolean;
  numberOfElements: number;
  empty: boolean;
}

// 5. 검색 필터 타입
export interface ReviewFilter {
  startDate: Date | null;
  endDate: Date | null;
}

// 6. 백엔드의 모든 응답 구조
export interface ApiResponse<T> {
  status: string;
  code: string;
  message: string;
  data: T; // 실제 우리가 필요한 데이터는 여기에 들어있음
}

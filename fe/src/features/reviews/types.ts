// 리뷰 이미지 정보를 표현하는 타입입니다.
export interface ReviewImage {
  imageId: string;
  imageUrl: string;
}

// 로컬 저장소에 보관하는 카페 리뷰 타입입니다.
export interface StoredCafeReview {
  id: string;
  rating: number;
  content: string;
  imageUrl: string;
  timestamp: number;
}

// 리뷰 목록 응답에 사용하는 리뷰 타입입니다.
export interface Review {
  reviewId: string;
  rating: number;
  content: string;
  createdAt: string;
  updatedAt: string;
  images: ReviewImage[];
  nickname: string;
  cafeName?: string;
}

// 리뷰 상세 응답에 사용하는 리뷰 타입입니다.
export interface ReviewDetailResponse {
  reviewId: string;
  rating: number;
  content: string;
  createdAt: string;
  updatedAt: string;
  imageUrls: string[];
  nickname: string;
  name: string;
  cafeIntro: string;
  address: string;
  roadAddress: string;
}

// 페이지네이션 정보를 표현하는 타입입니다.
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

// 내 리뷰 목록 응답에 사용하는 타입입니다.
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

// 카페 리뷰 이미지 응답에 사용하는 타입입니다.
export interface CafeReviewImageDto {
  imageId: string;
  imageUrl: string;
}

// 카페 리뷰 목록 항목에 사용하는 타입입니다.
export interface CafeReviewResponse {
  reviewId: string;
  rating: number;
  content: string;
  createdAt: string;
  updatedAt: string;
  images: CafeReviewImageDto[];
  nickname: string;
}

// 카페 리뷰 목록 응답에 사용하는 타입입니다.
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

// 리뷰 검색 필터에 사용하는 타입입니다.
export interface ReviewFilter {
  startDate: Date | null;
  endDate: Date | null;
}

// 공통 API 응답 래퍼에 사용하는 타입입니다.
export interface ApiResponse<T> {
  status: string;
  code: string;
  message: string;
  data: T;
}

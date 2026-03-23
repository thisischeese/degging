// features/users/types.ts
// 마이페이지 관련 API 응답/요청 데이터 구조(타입)를 정의하는 파일입니다.

// ─────────────────────────────────────────────────────────
// 1. 리뷰 데이터 구조 (내 리뷰 조회 API 응답 형태)
// ─────────────────────────────────────────────────────────
export interface ReviewContent {
  reviewId: string;
  rating: number;
  content: string;
  createdAt: string;
  updatedAt: string;
  thumbnailImage: string;
  cafeName: string;
}

export interface MyReviewResponse {
  content: ReviewContent[];
  totalElements?: number;
  totalPages?: number;
  size?: number;
  number?: number;
}

/** 2. 리뷰 아이템 컴포넌트 Props (UI용) */
export interface ReviewItem {
  reviewId: number | string;
  cafeId?: number;
  cafeName: string;
  cafeImageUrl: string;
  content: string;
  createdAt: string;
}

// ─────────────────────────────────────────────────────────
// 3. 유저 프로필 데이터 구조 (API 명세와 100% 일치)
// ─────────────────────────────────────────────────────────
export interface UserProfile {
  // 명세서에 id/userId가 없으므로 제거합니다.
  nickname: string;
  email: string;
  profileImageUrl: string | null;
  /** 백엔드 명세(온보딩)에 맞추어 preferredTags 사용 */
  preferredTags: string[];
  birthDate?: string;
  gender?: string;
}

/** 비밀번호 찾기 요청 데이터 */
export interface FindPasswordData {
  email: string;
}

/** 비밀번호 변경 요청 데이터 */
export interface ResetPasswordData {
  currentPassword?: string;
  newPassword?: string;
}
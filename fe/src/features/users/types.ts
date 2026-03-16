// features/users/types.ts
// 마이페이지 관련 API 응답/요청 데이터 구조(타입)를 정의하는 파일입니다.
// (features/auth/types.ts와 동일한 원리 - 데이터 '모양'만 정의합니다.)

// ─────────────────────────────────────────────────────────
// 1. 리뷰 1개(아이템)가 가진 데이터 구조
//    API 응답 시 서버가 보내줄 리뷰 1건의 형태를 미리 저장해 두는 인터페이스입니다.
// ─────────────────────────────────────────────────────────
export interface ReviewItem {
  /** 이 리뷰 고유 번호 (각 리뷰를 구별하는 ID) */
  reviewId: number;
  /** 리뷰가 달려있는 카페의 고유 번호 */
  cafeId: number;
  /** 카페 이름 */
  cafeName: string;
  /** 카페 대표 이미지 URL */
  cafeImageUrl: string;
  /** 리뷰 본문 내용 */
  content: string;
  /** 리뷰 작성 날짜 (예: "2026.03.04" 형식) */
  createdAt: string;
}

// ─────────────────────────────────────────────────────────
// 2. 유저 프로필 데이터 구조
//    마이페이지 상단의 프로필 정보 API 응답 형태입니다.
// ─────────────────────────────────────────────────────────
export interface UserProfile {
  /** 유저 고유 번호 */
  userId: number;
  /** 닉네임 (예: "oo님") */
  nickname: string;
  /** 이메일 주소 */
  email: string;
  /** 프로필 이미지 URL (없을 경우 기본 이미지 표시) */
  profileImageUrl: string | null;
  /** 유저가 자주 보는 해시태그 리스트 (예: ["#차분한", "#힙한", "#따뜻한"]) */
  topHashtags: string[];
  /** 생년월일 (예: "1999.02.12") */
  birthDate?: string;
  /** 성별 (예: "여") */
  gender?: string;
}

// 카페 메뉴 정보를 나타내는 타입
export interface Menu {
  menuId?: number;
  name?: string;
  menuName?: string;
  price: number | string | null;
  menuDescription?: string | null;
  image?: string | null;
  menuImageUrl?: string | null;
}

// 카페 상세 조회 응답 데이터 모델
export interface CafeDetailData {
  cafeId: string;
  name: string;
  cafeIntro?: string;
  rating: number;
  reviewCount: number;
  isScrapped: boolean;
  scrapColor: string | null;
  images: string[];
  vibeTags: string[];
  menus: Menu[];
  // 아래 필드는 명세에 없으나 UI에 필요할 수 있으므로 옵셔널로 처리
  description?: string;
  businessHours?: string;
  address?: string;
  roadAddress?: string;
  phone?: string;
}

// 카페 상세 조회 전체 응답 모델
export interface CafeDetailResponse {
  isSuccess: boolean;
  code: string;
  message: string;
  data: CafeDetailData;
}

// 통합 카페 검색 요청 모델
export interface SearchCafesRequest {
  keyword: string;
  latitude: number;
  longitude: number;
  mood?: string[]; // 복합 검색일 경우 추가됨
}

// 통합 카페 검색 응답 아이템 (마커 및 리스트 공통)
export interface SearchCafeItem {
  cafeId: string;
  name: string;
  address?: string;
  latitude: number;
  longitude: number;
  distance: number;
  cafeIntro?: string;
  thumbnailUrl?: string;
}

// 통합 카페 검색 전체 응답 모델
export interface SearchCafesResponse {
  isSuccess: boolean;
  code: string;
  message: string;
  data: {
    cafes: SearchCafeItem[];
  };
}

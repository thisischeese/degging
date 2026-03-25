// 실제 서버 API 연동을 위한 지도 범위 데이터 요청 객체입니다.
export interface CafeMapRequest {
  latitude: number;
  longitude: number;
  includeFranchise: boolean;
  tags?: string[]; // [추가] 취향 태그 필터링
}

// 마커 하나에 해당하는 데이터 객체입니다.
export interface CafeMarker {
  cafeId: string;
  latitude: number;
  longitude: number;
}

// 마커 API의 전체 응답 형태입니다. (분류된 마커 및 필터 추천 태그 포함)
export interface CafeMapResponse {
  isSuccess: boolean;
  code: string;
  message: string;
  data: {
    markers: CafeMarker[];
    filterTags: string[]; // [추가] 추천 태그 목록
  };
}

// 바텀시트 목록 조회를 위한 요청 객체입니다.
export interface CafeBottomSheetRequest {
  latitude: number;
  longitude: number;
  includeFranchise: boolean;
  sort: string;
  page: number;
  size: number;
}

// 바텀시트 목록의 개별 카페 아이템 객체입니다.
export interface CafeBottomSheetItem {
  cafeId: string;
  thumbnailUrl: string;
  name: string;
  cafeIntro: string;
  roadAddress: string;
  latitude: number;
  longitude: number;
}

// 바텀시트 API의 페이징 응답 형태입니다.
export interface CafeBottomSheetResponse {
  isSuccess: boolean;
  code: string;
  message: string;
  data: {
    content: CafeBottomSheetItem[];
    last: boolean;
  };
}

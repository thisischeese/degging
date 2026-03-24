// 실제 서버 API 연동을 위한 지도 범위 데이터 요청 객체입니다.
export interface CafeMapRequest {
  latitude: number;
  longitude: number;
  includeFranchise: boolean;
}

// 마커 하나에 해당하는 데이터 객체입니다.
export interface CafeMarker {
  cafeId: string;
  latitude: number;
  longitude: number;
}

// 마커 API의 전체 응답 형태입니다.
export interface CafeMapResponse {
  isSuccess: boolean;
  code: string;
  message: string;
  data: CafeMarker[];
}

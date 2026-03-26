import { axios_instance } from "@/api/axios_instance";
import { 
  CafeMapRequest, 
  CafeMapResponse, 
  CafeMarker, 
  CafeBottomSheetRequest, 
  CafeBottomSheetResponse 
} from "../types";

// [실제 API 연동] 지도의 중심(또는 사용자) 좌표와 프랜차이즈 포함 여부, 태그를 넘겨 카페 마커 목록을 조회합니다.
export const getCafeMarkers = async (params: CafeMapRequest): Promise<CafeMapResponse['data']> => {
  const response = (await axios_instance.get<CafeMapResponse>('/api/cafes/map/markers', {
    params: {
      ...params,
      tags: (params.tags || []).join(','), // 빈 배열일 경우 태그 파라미터 유실 방지를 위해 빈 문자열로, 값이 있으면 쉼표 분리 문자열로 변환
    },
  })) as unknown as CafeMapResponse;

  return response.data;
};

// [실제 API 연동] 지도 중심(또는 사용자) 좌표를 기준으로 바텀시트에 표시될 카페 목록을 페이징하여 조회합니다.
export const getCafeBottomSheetList = async (params: CafeBottomSheetRequest): Promise<CafeBottomSheetResponse['data']> => {
  const response = (await axios_instance.get<CafeBottomSheetResponse>('/api/cafes/map/bottom-sheet', {
    params: {
      ...params,
      tags: (params.tags || []).join(','), // 빈 배열 파라미터 유실 방지 처리
    },
  })) as unknown as CafeBottomSheetResponse;

  return response.data;
};

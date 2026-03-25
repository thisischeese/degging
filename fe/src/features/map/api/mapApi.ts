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
      tags: params.tags || [], // 빈 배열이 안정적으로 전달되도록 기본값 보장
    },
  })) as unknown as CafeMapResponse;

  return response.data;
};

// [실제 API 연동] 지도 중심(또는 사용자) 좌표를 기준으로 바텀시트에 표시될 카페 목록을 페이징하여 조회합니다.
export const getCafeBottomSheetList = async (params: CafeBottomSheetRequest): Promise<CafeBottomSheetResponse['data']> => {
  const response = (await axios_instance.get<CafeBottomSheetResponse>('/api/cafes/map/bottom-sheet', {
    params,
  })) as unknown as CafeBottomSheetResponse;

  return response.data;
};

import { axios_instance } from "@/api/axios_instance";
import { CafeMapRequest, CafeMapResponse, CafeMarker } from "../types";

// [실제 API 연동] 지도의 중심(또는 사용자) 좌표와 프랜차이즈 포함 여부를 넘겨 카페 마커 목록을 조회합니다.
export const getCafeMarkers = async (params: CafeMapRequest): Promise<CafeMarker[]> => {
  const response = (await axios_instance.get<CafeMapResponse>('/api/cafes/map/markers', {
    params,
  })) as unknown as CafeMapResponse;

  return response.data;
};

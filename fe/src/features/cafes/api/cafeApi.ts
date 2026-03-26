import { axios_instance } from "@/api/axios_instance";
import { CafeDetailResponse, SearchCafesRequest, SearchCafesResponse, SearchCafeItem } from "../types";

// [실제 API 연동] cafeId를 받아 카페의 상세 정보를 조회합니다.
export const getCafeDetail = async (cafeId: string): Promise<CafeDetailResponse['data']> => {
  const response = (await axios_instance.get<CafeDetailResponse>(`/api/cafes/${cafeId}`)) as unknown as CafeDetailResponse;
  
  return response.data;
};

// [실제 API 연동] 키워드, 내 위치, 그리고 조건(Mood)에 따라 카페를 검색합니다.
export const searchCafes = async (payload: SearchCafesRequest): Promise<SearchCafeItem[]> => {
  // 복합 조건(mood)이 있을 경우 POST, 단순 키워드 검색일 경우 GET 사용
  if (payload.mood && payload.mood.length > 0) {
    const response = await axios_instance.post<SearchCafesResponse>(`/api/cafes/search`, payload) as unknown as SearchCafesResponse;
    // 응답이 data 배열 형태일 수도 있고, data.cafes 일 수도 있으므로 방어적 접근
    return Array.isArray(response.data) ? response.data : (response.data?.cafes || []);
  } else {
    const response = await axios_instance.get<SearchCafesResponse>(`/api/cafes/search`, {
      params: {
        keyword: payload.keyword,
        latitude: payload.latitude,
        longitude: payload.longitude,
      }
    }) as unknown as SearchCafesResponse;
    return Array.isArray(response.data) ? response.data : (response.data?.cafes || []);
  }
};

import { axios_instance } from "@/api/axios_instance";
import { CafeDetailResponse } from "../types";

// [실제 API 연동] cafeId를 받아 카페의 상세 정보를 조회합니다.
export const getCafeDetail = async (cafeId: string): Promise<CafeDetailResponse['data']> => {
  const response = (await axios_instance.get<CafeDetailResponse>(`/api/cafes/${cafeId}`)) as unknown as CafeDetailResponse;
  
  return response.data;
};

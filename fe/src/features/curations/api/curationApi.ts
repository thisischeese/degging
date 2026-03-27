import { axios_instance } from "@/api/axios_instance";
import {
  CurationMinimapResponse,
  CurationCafeListResponse,
} from "../types";

/**
 * 각 카페 미니맵 조회
 * GET /api/curation/minimap
 * @param category - 큐레이션 카테고리 (예: "두쫀쿠", "소금빵 카페", "망고빙수", "딸기 케이크")
 * @param cafeName - 카페 이름 (예: "카페구움")
 */
export const getCurationMinimap = async (
  category: string,
  cafeName: string
): Promise<CurationMinimapResponse> => {
  return await axios_instance.get("/api/curation/minimap", {
    params: { category, cafeName },
  });
};

/**
 * 카테고리별 카페 리스트 조회
 * GET /api/curation/cafeList
 * @param category - 큐레이션 카테고리 (예: "두쫀쿠", "소금빵 카페", "망고빙수", "딸기 케이크")
 */
export const getCurationCafeList = async (
  category: string
): Promise<CurationCafeListResponse> => {
  return await axios_instance.get("/api/curation/cafeList", {
    params: { category },
  });
};

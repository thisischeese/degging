import { axios_instance } from "@/api/axios_instance";
import { RankingResponse } from "../types";

/**
 * 실시간 디저트 랭킹 조회
 * GET /api/ranks/desserts
 */
export const getRealTimeRankings = async (): Promise<RankingResponse> => {
  return await axios_instance.get("/api/ranks/desserts");
};

/**
 * 온보딩 페이지 애착메뉴 조회 (실시간 디저트 랭킹 상위 20개)
 * GET /api/ranks/desserts/onboarding
 */
export const getOnboardingRankings = async (): Promise<RankingResponse> => {
  return await axios_instance.get("/api/ranks/desserts/onboarding");
};

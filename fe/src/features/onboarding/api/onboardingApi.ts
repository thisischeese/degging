import { axios_instance } from "@/api/axios_instance";
import { BaseResponse } from "@/features/auth/types";
import { OnboardingCafe, OnboardingResult, OnboardingInitialData } from "../types";

/** 온보딩 페이지 애착메뉴 조회 */
export const getOnboardingMenus = async (): Promise<string[]> => {
  const response = await axios_instance.get<BaseResponse<{ menuNames: string[] }>>('/api/ranks/desserts/onboarding');
  const baseResponse = response as unknown as BaseResponse<{ menuNames: string[] }>;
  return baseResponse.data.menuNames;
};

/** 온보딩 페이지 카페 이미지 조회 */
export const getOnboardingCafes = async (): Promise<OnboardingCafe[]> => {
  const response = await axios_instance.get<BaseResponse<OnboardingCafe[]>>('/api/cafes/onboarding');
  const baseResponse = response as unknown as BaseResponse<OnboardingCafe[]>;
  return baseResponse.data;
};

/** 온보딩 결과 반환 - 응답 data가 null이므로 반환값 불필요 */
export const postOnboardingResults = async (data: OnboardingResult): Promise<void> => {
  await axios_instance.post('/api/users/onboarding', data);
};

/** 사용자 취향 초기화 */
export const postOnboardingReset = async (data: OnboardingInitialData) => {
  const response = await axios_instance.post('/ai/onboarding', data);
  return response.data;
};

import { axios_instance } from "@/api/axios_instance";
import { OnboardingMenu, OnboardingCafe, OnboardingResult, OnboardingInitialData } from "../types";

/** 온보딩 페이지 애착메뉴 조회 */
export const getOnboardingMenus = async (): Promise<OnboardingMenu[]> => {
  const response = await axios_instance.get('/api/ranks/desserts/onboarding');
  return response.data; // ✅ .data 한 번만 (이전: .data.data 였음 → 버그)
};

/** 온보딩 페이지 카페 이미지 조회 */
export const getOnboardingCafes = async (): Promise<OnboardingCafe[]> => {
  const response = await axios_instance.get('/api/cafes/onboarding');
  return response.data; // ✅ .data 한 번만
};

/** 온보딩 결과 반환 - 응답 data가 null이므로 반환값 불필요 */
export const postOnboardingResults = async (data: OnboardingResult): Promise<void> => {
  await axios_instance.post('/api/users/onboarding', data);
};

/** 사용자 취향 초기화 */
export const postOnboardingReset = async (data: OnboardingInitialData) => {
  const response = await axios_instance.post('/api/ai/onboarding', data);
  return response.data;
};

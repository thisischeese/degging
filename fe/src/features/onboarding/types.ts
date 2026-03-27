// features/onboarding/types.ts

export interface OnboardingMenu {
  id: number;
  rank: number;
  keyword: string;
}

export interface OnboardingCafe {
  cafeId: string;
  thumbnailUrl: string;
}

export interface OnboardingResult {
  onboardingToken: string;
  cafeIds: string[];
  menuIds: number[];
}

export interface OnboardingInitialData {
  user_id: string;
  favorite_menu_ids: number[];
  favorite_cafe_ids: number[];
}

// features/onboarding/types.ts

export interface OnboardingMenu {
  rank: number;
  keyword: string;
}

export interface OnboardingCafe {
  cafeId: string;
  thumbnailUrl: string;
}

export interface OnboardingResult {
  selectedCafeIds: string[];
  preferredTags: string[];
}

export interface OnboardingInitialData {
  user_id: string;
  favorite_menu_ids: number[];
  favorite_cafe_ids: number[];
}

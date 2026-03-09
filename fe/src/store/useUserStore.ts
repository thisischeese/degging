import { create } from 'zustand';

// 1. 보관함에 담을 데이터와 함수의 '설계도'
interface UserState {
  is_logged_in: boolean;          // 로그인 여부
  nickname: string;             // 유저 이름
  profile_image_url: string;      // 프로필 이미지 URL
  user_group: 'A' | 'B' | null;  // A/B 테스트 그룹 
  
  // 상태를 변경하는 함수들
  set_login: (data: { nickname: string; profile_image_url?: string; group?: 'A' | 'B' }) => void;
  set_logout: () => void;
}

// 2. 실제 보관함(Store)을 생성
export const useUserStore = create<UserState>((set) => ({
  // 초기값 설정
  is_logged_in: false,
  nickname: '',
  profile_image_url: '',
  user_group: null,

  // 로그인 성공 시 데이터를 채우는 함수
  set_login: (data) => set({ 
    is_logged_in: true, 
    nickname: data.nickname, 
    profile_image_url: data.profile_image_url || '',
    user_group: data.group || null 
  }),

  // 로그아웃 시 데이터를 비우는 함수
  set_logout: () => set({ 
    is_logged_in: false, 
    nickname: '', 
    profile_image_url: '', 
    user_group: null 
  }),
}));
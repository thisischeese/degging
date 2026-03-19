export interface SignupFormData {
  email: string;
  password?: string;
  name?: string;
  nickname?: string;
  birthDate?: string;
  gender?: "MALE" | "FEMALE";
  trends?: string[];
  moods?: string[];
}

export interface SignupStepProps {
  /** 다음 단계로 이동하는 함수 */
  next: () => void;
  /** 이전 단계로 이동하는 함수 (선택 사항) */
  prev?: () => void;
  /** 현재까지 입력된 전체 데이터 */
  formData: SignupFormData;
  /** 데이터를 업데이트하는 함수 (Partial을 사용하여 일부만 업데이트 가능) */
  updateData: (newData: Partial<SignupFormData>) => void;
}

/** 로그인 요청 데이터 */
export interface LoginFormData {
  email: string;
  password?: string; // 소셜 로그인의 경우 비밀번호가 없을 수 있어 ?를 붙이기도 합니다.
}

/** 로그인 성공 시 서버에서 내려주는 응답 데이터 구조 (예시) */
export interface LoginResponse {
  status: string;
  code: string;
  message: string;
  data: {
    accessToken: string;
    refreshToken: string;
    user: {
      id: number;
      email: string;
      nickname: string;
    };
  };
}

/** 비밀번호 찾기 요청 데이터 */
export interface FindPasswordData {
  email: string;
}
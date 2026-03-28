export type Gender = 'MALE' | 'FEMALE';

/** 1. 실제 백엔드 회원가입 요청 시 보내는 데이터 */
export interface SignupRequest {
  email: string;
  password: string;
  nickname: string;
  gender: Gender;
  birthDate: string; // "1111-11-11"
}

/** 2. 프론트엔드 회원가입 단계(Step1~5)에서 관리하는 전체 데이터 */
export interface SignupFormData extends SignupRequest {
  trends: string[]; // 온보딩용 (메뉴 명칭)
  moods: string[]; // 온보딩용 (카페 UUID)
}

export interface SignupStepProps {
  /** 다음 단계로 이동하는 함수 */
  next: (data?: unknown) => void;
  /** 이전 단계로 이동하는 함수 (선택 사항) */
  prev?: () => void;
  /** 현재까지 입력된 전체 데이터 */
  formData: SignupFormData;
  /** 데이터를 업데이트하는 함수 (Partial을 사용하여 일부만 업데이트 가능) */
  updateData: (newData: Partial<SignupFormData>) => void;
  /** 부모의 공통 알럿 모달을 여는 콜백 */
  onAlert?: (title: string, message?: string) => void;
}

/** 로그인 요청 데이터 */
export interface LoginFormData {
  email: string;
  password?: string; // 소셜 로그인의 경우 비밀번호가 없을 수 있어 ?를 붙이기도 합니다.
}

/** 로그인 성공 시 서버에서 내려주는 응답 데이터 구조 */
export interface LoginResponseData {
  accessToken: string;
  refreshToken: string;
}

export interface BaseResponse<T> {
  code: number | string;
  message: string;
  data: T;
}

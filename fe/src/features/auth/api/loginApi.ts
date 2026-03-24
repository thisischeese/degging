import { axios_instance } from "@/api/axios_instance";
import { LoginFormData, LoginResponseData, BaseResponse } from "../types";
import Cookies from "js-cookie";

export const postLogin = async (formData: LoginFormData): Promise<LoginResponseData> => {
  const response = await axios_instance.post<BaseResponse<LoginResponseData>>('/api/auth/login', formData);
  
  // axios_instance.interceptors.response.use((response) => response.data) 가 설정되어 있으므로
  // response는 실제로는 BaseResponse 객체입니다.
  const baseResponse = response as unknown as BaseResponse<LoginResponseData>;
  
  // 로그인 성공 시 쿠키에도 저장 (미들웨어용)
  if (baseResponse.data?.accessToken) {
    Cookies.set("access_token", baseResponse.data.accessToken, { 
      // expires: 7, // 7일간 유지
      path: "/",
      secure: process.env.NODE_ENV === "production",
      sameSite: "Lax"
    });
  }

  return baseResponse.data; 
};

/** 로그아웃 (토큰 및 쿠키 제거) */
export const postLogout = async () => {
  try {
    await axios_instance.post('/api/auth/logout');
  } finally {
    // 성공 여부와 상관없이 클라이언트 데이터는 비워야 합니다.
    Cookies.remove("access_token", { path: "/" });
    Cookies.remove("refresh_token", { path: "/" });
    
    if (typeof window !== 'undefined') {
      window.location.href = '/onboarding';
    }
  }
};
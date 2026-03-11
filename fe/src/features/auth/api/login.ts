import { axios_instance } from "@/api/axios_instance";
import { LoginFormData } from "../types"; // types 파일에 이메일, 비번 인터페이스가 있다고 가정

export const postLogin = async (formData: LoginFormData) => {
  // 1. 테스트용 (백엔드 연결 전)
  console.log("로그인 시도 데이터:", formData);
  
  // 가짜 응답 생성 (1초 뒤 성공)
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ 
        status: 200, 
        data: { token: "fake-jwt-token", user: { name: "최지희" } } 
      });
    }, 1000);
  });

  /* // 2. 실제 백엔드 연결 시
  const response = await axios_instance.post('/api/auth/login', formData);
  return response.data; 
  */
};
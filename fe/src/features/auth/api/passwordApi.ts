import { axios_instance } from "@/api/axios_instance";
import { FindPasswordData } from "../types";

export const postFindPassword = async (data: FindPasswordData) => {
  console.log("비밀번호 찾기 요청:", data);
  
  // 테스트용 가짜 응답
  return new Promise((resolve) => {
    setTimeout(() => resolve({ status: 200 }), 1000);
  });

  /* 실제 연결 시
  return await axios_instance.post('/api/auth/find-password', data);
  */
};
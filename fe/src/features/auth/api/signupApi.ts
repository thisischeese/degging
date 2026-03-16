import { axios_instance } from "@/api/axios_instance"; // 아까 만드신 인스턴스
import { SignupFormData } from "../types";

export const postSignup = async (formData: SignupFormData) => {
  // 1. 테스트용 (백엔드 없을 때)
  console.log("서버로 보낼 데이터:", formData);
  return new Promise((resolve) => {
    setTimeout(() => resolve({ status: 200 }), 2000);
  });

  // 2. 실제 백엔드 연결 시 (주소가 나오면 위 테스트용은 지우고 아래 주석을 푸세요)
  // const response = await axios_instance.post('/api/auth/signup', formData);
  // return response;
};
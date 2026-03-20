import { axios_instance } from "@/api/axios_instance"; // 아까 만드신 인스턴스
import { SignupFormData } from "../types";

interface SignupResponse {
  message: string;
}

export const postSignup = async (formData: SignupFormData): Promise<SignupResponse> => {
  const response = await axios_instance.post<SignupResponse>('/api/auth/signup', formData);
  return response.data;
};
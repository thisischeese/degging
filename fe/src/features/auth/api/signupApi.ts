import { axios_instance } from "@/api/axios_instance"; // 아까 만드신 인스턴스
import { SignupFormData } from "../types";

export const postSignup = async (formData: SignupFormData) => {
  const response = await axios_instance.post('/api/auth/signup', formData);
  return response;
};
import { axios_instance } from "@/api/axios_instance";
import { LoginFormData } from "../types"; // types 파일에 이메일, 비번 인터페이스가 있다고 가정

export const postLogin = async (formData: LoginFormData) => {
  const response = await axios_instance.post('/api/auth/login', formData);
  return response.data; 
};
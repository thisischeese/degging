import { axios_instance } from "@/api/axios_instance";
import { LoginFormData, LoginResponseData, BaseResponse } from "../types";

export const postLogin = async (formData: LoginFormData): Promise<LoginResponseData> => {
  const response = await axios_instance.post<BaseResponse<LoginResponseData>>('/api/auth/login', formData);
  // axios_instance.interceptors.response.use((response) => response.data) 가 설정되어 있으므로
  // response는 실제로는 BaseResponse 객체입니다.
  const baseResponse = response as unknown as BaseResponse<LoginResponseData>;
  return baseResponse.data; 
};
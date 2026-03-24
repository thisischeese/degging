import { axios_instance } from "@/api/axios_instance";
import { SignupRequest, BaseResponse } from "../types";

export const postSignup = async (formData: SignupRequest): Promise<BaseResponse<{ onboardingToken?: string }>> => {
  const response = await axios_instance.post<BaseResponse<{ onboardingToken?: string }>>('/api/auth/signup', formData);
  return response as unknown as BaseResponse<{ onboardingToken?: string }>;
};
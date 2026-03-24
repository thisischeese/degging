import { axios_instance } from "@/api/axios_instance";
import { FindPasswordData, ResetPasswordData } from "../types";

export const postFindPassword = async (data: FindPasswordData) => {
  const response = await axios_instance.post('/api/auth/password/find', data);
  // axios_instance가 response.data를 반환하므로, response는 BaseResponse 객체입니다.
  return response;
};

export const patchResetPassword = async (data: ResetPasswordData) => {
  const response = await axios_instance.post('/api/user/password/reset', data);
  return response;
};
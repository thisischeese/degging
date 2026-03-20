import { axios_instance } from "@/api/axios_instance";
import { FindPasswordData, ResetPasswordData } from "../types";

export const postFindPassword = async (data: FindPasswordData) => {
  const response = await axios_instance.post('/api/user/password/find', data);
  return response.data;
};

export const patchResetPassword = async (data: ResetPasswordData) => {
  const response = await axios_instance.patch('/api/user/password/reset', data);
  return response.data;
};
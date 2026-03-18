import { axios_instance } from "@/api/axios_instance";
import { FindPasswordData } from "../types";

export const postFindPassword = async (data: FindPasswordData) => {
  return await axios_instance.post('/api/auth/password/find', data);
};
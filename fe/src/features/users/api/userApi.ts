import { axios_instance } from "@/api/axios_instance";

export const getUserInfo = async () => {
  const response = await axios_instance.get('/api/users');
  return response;
};
import { axios_instance } from "@/api/axios_instance";
import { BaseResponse } from "@/features/auth/types";

/** 1. 비밀번호 찾기 (임시 비밀번호 발송) */
export const postPasswordFind = async (email: string): Promise<BaseResponse<null>> => {
    const response = await axios_instance.post('/api/user/password/find', { email });
    return response as unknown as BaseResponse<null>;
};

/** 2. 비밀번호 변경 */
export const patchPasswordReset = async (currentPassword: string, newPassword: string): Promise<BaseResponse<null>> => {
    const response = await axios_instance.patch('/api/user/password/reset', { currentPassword, newPassword });
    return response as unknown as BaseResponse<null>;
};

/** 3. 사용자 정보 조회 */
export const getUserInfo = async () => {
    const response = await axios_instance.get('/api/users');
    return response; 
};

/** 4. 사용자 정보 수정 */
export const patchUsers = async (data: { nickname?: string; profile_image_url?: string }) => {
    const response = await axios_instance.patch('/api/users', data);
    return response;
};

/** 5. 사용자 정보 삭제 (탈퇴) */
export const deleteUsers = async () => {
    const response = await axios_instance.delete('/api/users');
    return response;
};

/** 6. A/B 테스트 전환 */
export const getAbTestJoin = async () => {
    const response = await axios_instance.get('/api/ab-tests/join');
    return response;
};
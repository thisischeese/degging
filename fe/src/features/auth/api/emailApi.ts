import { axios_instance } from "@/api/axios_instance";
import { BaseResponse } from "../types";

/** 1. 이메일 인증 코드 발송 요청 */
export const postEmailVerificationRequest = async (email: string): Promise<BaseResponse<null>> => {
    const response = await axios_instance.post('/api/auth/email/verification/request', { email });
    return response as unknown as BaseResponse<null>;
};

/** 2. 이메일 인증 코드 확인 */
export const postEmailVerificationConfirm = async (email: string, code: string): Promise<BaseResponse<null>> => {
    const response = await axios_instance.post('/api/auth/email/verification/confirm', { email, code });
    return response as unknown as BaseResponse<null>;
};

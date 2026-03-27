import { axios_instance } from "@/api/axios_instance";
import { BaseResponse } from "@/features/auth/types";
import { UserProfile, ResetPasswordData, MyReviewResponse, FindPasswordData } from "../types";

/** 1. 사용자 정보 조회 (명세서와 일치하는 데이터 반환) */
export const getUserInfo = async (): Promise<BaseResponse<UserProfile>> => {
    // any 없이 unknown 캐스팅으로 인터셉터가 언래핑한 데이터를 안전하게 반환합니다.
    return axios_instance.get<BaseResponse<UserProfile>>('/api/users') as unknown as Promise<BaseResponse<UserProfile>>;
};

/** 2. 내 리뷰 전체 조회 */
export const getMyReviews = async (page: number = 0, size: number = 5): Promise<BaseResponse<MyReviewResponse>> => {
    return axios_instance.get<BaseResponse<MyReviewResponse>>('/api/reviews/mine', {
        params: { page, size }
    }) as unknown as Promise<BaseResponse<MyReviewResponse>>;
};

/** 3. 사용자 정보 수정 (닉네임, 프로필 이미지) */
export const patchUsers = async (data: { nickname: string; profileImage?: File | null; defaultImage: boolean }): Promise<BaseResponse<UserProfile>> => {
    const formData = new FormData();
    formData.append('nickname', data.nickname);
    
    if (data.profileImage) {
        formData.append('profileImage', data.profileImage);
    }
    
    formData.append('defaultImage', String(data.defaultImage));

    return axios_instance.patch<BaseResponse<UserProfile>>('/api/users', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }) as unknown as Promise<BaseResponse<UserProfile>>;
};

/** 4. 비밀번호 변경 */
export const patchPasswordReset = async (data: ResetPasswordData): Promise<BaseResponse<null>> => {
    return axios_instance.patch<BaseResponse<null>>('/api/users/password/reset', data) as unknown as Promise<BaseResponse<null>>;
};

/** 5. 사용자 정보 삭제 (탈퇴) */
export const deleteUsers = async (): Promise<BaseResponse<null>> => {
    return axios_instance.delete<BaseResponse<null>>('/api/users') as unknown as Promise<BaseResponse<null>>;
};

/** 7. 비밀번호 찾기 (임시 비밀번호 이메일 발송) */
export const postFindPassword = async (data: FindPasswordData): Promise<BaseResponse<null>> => {
    return axios_instance.post<BaseResponse<null>>('/api/auth/password/find', data) as unknown as Promise<BaseResponse<null>>;
};

/** 8. 취향 태그 조회 */
export const getUserPreferences = async (): Promise<string[]> => {
    const response = await axios_instance.get<BaseResponse<string[]>>('/api/users/preferences') as unknown as BaseResponse<string[]>;
    return response.data;
};
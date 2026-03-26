import { axios_instance } from "@/api/axios_instance";
import { BaseResponse } from "@/types/api";
import { DiscoverySliceResponse } from "../types";

/**
 * 탐색 탭 메인 화면 진입 및 무한 스크롤용 - 일일 랜덤 카페 리스트 조회
 * GET /api/discovery
 */
export const getDiscoveryCafes = async (page: number = 0, size: number = 15): Promise<DiscoverySliceResponse> => {
    const response = (await axios_instance.get<BaseResponse<DiscoverySliceResponse>>("/api/discovery", {
        params: { page, size },
    })) as unknown as BaseResponse<DiscoverySliceResponse>;

    return response.data;
};

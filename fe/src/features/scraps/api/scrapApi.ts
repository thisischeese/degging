import { axios_instance } from "@/api/axios_instance";
import { ScrapList, ScrapDetail, StarColor } from "../types";

/** (완료) 카페 스크랩 추가 */
export const postScrapCafe = async (scrapId: string, cafeId: string) => {
    const response = await axios_instance.post(`/api/scraps/${scrapId}/cafes/${cafeId}`);
    return response.data;
};

/** (완료) 카페 스크랩 취소 */
export const deleteScrapCafe = async (scrapId: string, cafeId: string) => {
    const response = await axios_instance.delete(`/api/scraps/${scrapId}/cafes/${cafeId}`);
    return response.data;
};

/** (완료) 새로운 스크랩 카테고리 생성 */
export const postCreateScrap = async (data: { name: string; color: StarColor }) => {
    const response = await axios_instance.post('/api/scraps', data);
    return response.data;
};

/** (완료) 내 스크랩 카테고리 목록 조회 */
export const getScraps = async (): Promise<ScrapList[]> => {
    const response = await axios_instance.get('/api/scraps');
    return response.data;
};

/** (완료) 특정 카테고리 상세 조회 (카페 리스트 포함) */
export const getScrapDetail = async (scrapId: string): Promise<ScrapDetail> => {
    const response = await axios_instance.get(`/api/scraps/${scrapId}`);
    return response.data;
};

/** (완료) 카테고리 이름 또는 색상 수정 */
export const patchUpdateScrap = async (scrapId: string, data: { name: string; color: StarColor }) => {
    const response = await axios_instance.patch(`/api/scraps/${scrapId}`, data);
    return response.data;
};

/** (완료) 카테고리 삭제 */
export const deleteScrap = async (scrapId: string) => {
    const response = await axios_instance.delete(`/api/scraps/${scrapId}`);
    return response.data;
};

/** (완료) 카테고리 추천 (공유 링크 생성) */
export const postShareLink = async (scrapId: string): Promise<{ shareLink: string }> => {
    const response = await axios_instance.post(`/api/scraps/${scrapId}/share-links`);
    return response.data;
};

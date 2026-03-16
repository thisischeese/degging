import { axios_instance } from "@/api/axios_instance";
import { MyReviewsResponse } from "../types";

/**
 * 내 리뷰 전체 조회 API
 * @param page 페이지 번호 (0부터 시작)
 * @param size 한 페이지당 크기
 * @param startDate 시작일 (YYYY-MM-DD 형식 문자열)
 * @param endDate 종료일 (YYYY-MM-DD 형식 문자열)
 */
export const getMyReviews = async (
  page: number = 0,
  size: number = 10,
  startDate?: string,
  endDate?: string
): Promise<MyReviewsResponse> => {
  const params: Record<string, string | number> = { page, size };
  
  if (startDate) params.startDate = startDate;
  if (endDate) params.endDate = endDate;

  const response = await axios_instance.get<MyReviewsResponse>("/api/reviews/mine", {
    params,
  });
  
  return response.data;
};

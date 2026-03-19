import { axios_instance } from "@/api/axios_instance";
import { BaseResponse } from "@/types/api";
import {
  ApiResponse,
  CafeReviewsSliceResponse,
  MyReviewsResponse,
  Review,
  StoredCafeReview,
} from "../types";

export const getMyReviews = async (
  page: number = 0,
  size: number = 10,
  startDate?: string,
  endDate?: string
): Promise<MyReviewsResponse> => {
  const getLocalReviews = (): Review[] => {
    if (typeof window === "undefined") return [];

    const allLocalReviews: Review[] = [];

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);

      if (key && (key.startsWith("cafeReviews-") || key === "cafeReviews-mock")) {
        try {
          const rawData = localStorage.getItem(key);
          if (!rawData) continue;

          const items: StoredCafeReview[] = JSON.parse(rawData);

          items.forEach((item) => {
            allLocalReviews.push({
              reviewId: item.id,
              rating: item.rating,
              content: item.content,
              createdAt: item.timestamp
                ? new Date(item.timestamp).toISOString()
                : new Date().toISOString(),
              updatedAt: new Date().toISOString(),
              nickname: "킴싸피",
              images: [{ imageId: `local-${item.id}`, imageUrl: item.imageUrl }],
              cafeName: "카페",
            });
          });
        } catch (error) {
          console.error("Failed to parse local reviews:", error);
        }
      }
    }

    return allLocalReviews;
  };

  // 2. 기본 하드코딩 Mock 데이터 (ID 중복 테스트용)
  const baseMockContent: Review[] = [
    {
      reviewId: "eed475e0-424d-4ae4-ac49-cc2e1119d167",
      rating: 5,
      content: "카페가 정말 예쁘네요!~~~~~~~~",
      createdAt: "2026-03-12T17:12:49.718464",
      updatedAt: "2026-03-12T17:12:49.718464",
      nickname: "킴싸피",
      images: [
        { imageId: "1", imageUrl: "/images/cafe/cafe1.png" },
        { imageId: "2", imageUrl: "/images/cafe/cafe2.png" },
      ],
      cafeName: "카페",
    },
  ];

  // 3. [데이터 병합 및 중복 제거] ID 기준
  const localData = getLocalReviews();
  let combinedContent = [
    ...localData,
    ...baseMockContent.filter((mockItem) => !localData.some((localItem) => localItem.reviewId === mockItem.reviewId)),
  ];

  // 4. [날짜 필터링]
  if (startDate || endDate) {
    combinedContent = combinedContent.filter((review) => {
      const reviewDate = review.createdAt.split("T")[0];
      if (startDate && reviewDate < startDate) return false;
      if (endDate && reviewDate > endDate) return false;
      return true;
    });
  }

  // 최신순 정렬
  combinedContent.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

  const mockResponse: MyReviewsResponse = {
    content: combinedContent.slice(page * size, (page + 1) * size),
    pageable: {
      pageNumber: page,
      pageSize: size,
      sort: { empty: false, sorted: true, unsorted: false },
      offset: page * size,
      unpaged: false,
      paged: true,
    },
    size,
    number: page,
    sort: { empty: false, sorted: true, unsorted: false },
    first: page === 0,
    last: (page + 1) * size >= combinedContent.length,
    numberOfElements: combinedContent.length,
    empty: combinedContent.length === 0,
  };

  try {
    const params: Record<string, string | number> = { page, size };
    if (startDate) params.startDate = startDate;
    if (endDate) params.endDate = endDate;

    const response = (await axios_instance.get<ApiResponse<MyReviewsResponse>>("/api/reviews/mine", {
      params,
    })) as unknown as ApiResponse<MyReviewsResponse>;

    return response.data;
  } catch (error) {
    console.warn("Falling back to mock my-reviews data:", error);
    return mockResponse;
  }
};

export const getCafeReviews = async (
  cafeId: string,
  page: number = 0,
  size: number = 10
): Promise<CafeReviewsSliceResponse> => {
  const response = (await axios_instance.get<BaseResponse<CafeReviewsSliceResponse>>(
    `/api/cafes/${cafeId}/reviews`,
    {
      params: { page, size },
    }
  )) as unknown as BaseResponse<CafeReviewsSliceResponse>;

  return response.data;
};

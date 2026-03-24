import { axios_instance } from "@/api/axios_instance";
import { BaseResponse } from "@/types/api";
import {
  ApiResponse,
  CafeReviewsSliceResponse,
  MyReviewsResponse,
  Review,
  ReviewDetailResponse,
  StoredCafeReview,
  PostReviewResponse,
} from "../types";

// 로컬 저장 리뷰를 내 리뷰 목록 형식으로 변환합니다.
const getLocalReviews = (): Review[] => {
  if (typeof window === 'undefined') {
    return [];
  }

  const allLocalReviews: Review[] = [];

  for (let index = 0; index < localStorage.length; index += 1) {
    const key = localStorage.key(index);

    if (!key || (!key.startsWith('cafeReviews-') && key !== 'cafeReviews-mock')) {
      continue;
    }

    try {
      const rawData = localStorage.getItem(key);

      if (!rawData) {
        continue;
      }

      const items: StoredCafeReview[] = JSON.parse(rawData);

      items.forEach((item) => {
        allLocalReviews.push({
          reviewId: item.id,
          rating: item.rating,
          content: item.content,
          createdAt: item.timestamp ? new Date(item.timestamp).toISOString() : new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          nickname: "킴싸피",
          images: item.imageUrl ? [{ imageId: `local-${item.id}`, imageUrl: item.imageUrl }] : [],
          cafeName: "카페",
        });
      });
    } catch (error) {
      console.error("Failed to parse local reviews:", error);

    }
  }

  return allLocalReviews;
};

// 기본 내 리뷰 목업 데이터를 정의합니다.
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

// 내 리뷰 목록을 조회하는 함수입니다.
export const getMyReviews = async (
  page: number = 0,
  size: number = 10,
  startDate?: string,
  endDate?: string
): Promise<MyReviewsResponse> => {
  const localData = getLocalReviews();

  let combinedContent = [
    ...localData,
    ...baseMockContent.filter(
      (mockItem) => !localData.some((localItem) => localItem.reviewId === mockItem.reviewId)
    ),
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

  combinedContent.sort((first, second) => {
    return new Date(second.createdAt).getTime() - new Date(first.createdAt).getTime();
  });

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

// [실제 API 연동] 카페 리뷰 목록을 서버에서 조회하는 함수입니다.
// page, size, 그리고 정렬 옵션(sort)을 쿼리 파라미터로 넘겨 실제 데이터를 가져옵니다.
export const getCafeReviews = async (
  cafeId: string,
  page: number = 0,
  size: number = 10,
  sort?: string[]
): Promise<CafeReviewsSliceResponse> => {
  const response = (await axios_instance.get<BaseResponse<CafeReviewsSliceResponse>>(
    `/api/cafes/${cafeId}/reviews`,
    {
      params: { page, size, sort }, // 정렬(sort) 파라미터 추가
    }
  )) as unknown as BaseResponse<CafeReviewsSliceResponse>;

  return response.data; // 서버 응답에서 실제 데이터(content, hasNext, page)만 추출하여 반환
};

export interface PostCafeReviewPayload {
  cafeId: string;
  rating: number;
  content: string;
  // 사용자가 <input type="file">로 선택한 실제 파일 객체들인 경우
  images?: File[]; // 이미지 배열 (필요에 따라 타입 수정)
}

// [실제 API 연동] 카페에 새로운 리뷰를 등록하는 함수입니다.
// 별점, 리뷰 내용, 이미지 목록을 담아 서버에 POST 요청을 보냅니다.
export const postCafeReview = async (
  cafeId: string,
  payload: PostCafeReviewPayload
): Promise<PostReviewResponse> => {
  // 파일 전송을 위해 FormData 객체를 생성합니다.
  const formData = new FormData();
  formData.append('rating', payload.rating.toString());
  formData.append('content', payload.content);
  formData.append('cafeId', payload.cafeId);

  // 이미지가 존재할 경우 FormData에 순차적으로 추가합니다.
  if (payload.images && payload.images.length > 0) {
    payload.images.forEach((file) => {
      formData.append('images', file);
    });
  }
  const response = (await axios_instance.post<BaseResponse<PostReviewResponse>>(
    `/api/cafes/${cafeId}/reviews`,
    formData,
    {
      headers: {  'Content-Type': 'multipart/form-data' }, // 파일 업로드를 위한 헤더 설정
    } 
  )) as unknown as BaseResponse<PostReviewResponse>;

  return response.data; // 등록된 리뷰 상세 데이터(reviewId 포함)를 반환
};

// 리뷰 상세 데이터를 조회하는 함수입니다.
export const getReviewDetail = async (reviewId: string): Promise<ReviewDetailResponse> => {
  const response = (await axios_instance.get<BaseResponse<ReviewDetailResponse>>(
    `/api/reviews/${reviewId}`
  )) as unknown as BaseResponse<ReviewDetailResponse>;

  return response.data;
};

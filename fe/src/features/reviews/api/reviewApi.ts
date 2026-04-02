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

    /* 기존 코드 보존
    return response.data;
    */

    // [수정] 내 리뷰 목록 썸네일 경로에 BaseURL 결합 처리
    const responseData = response.data;
    const baseUrl = (process.env.NEXT_PUBLIC_CLOUDFRONT_URL || '').replace(/\/$/, '');

    const transformedContent = responseData.content.map((review: Review) => {
      const rawPath = review.thumbnailImage;
      // 주소가 이미 http로 시작하면 그대로 두고, 아니면 baseUrl을 강제로 결합
      const fullUrl = (rawPath && !rawPath.startsWith('http') && !rawPath.startsWith('blob:'))
        ? `${baseUrl}/${rawPath.startsWith('/') ? rawPath.slice(1) : rawPath}`
        : rawPath || '/images/common/logo.png';

      return { ...review, thumbnailImage: fullUrl };
    });

    // [추가/수정] 서버 데이터 조회 성공 시 로컬 중복(유령) 데이터 완전 제거 방어 로직
    if (typeof window !== 'undefined' && responseData && Array.isArray(responseData.content)) {
      const serverIds = responseData.content.map((r: Review) => r.reviewId);
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('cafeReviews-')) {
          try {
            const raw = localStorage.getItem(key);
            const localReviews = raw ? JSON.parse(raw) : [];
            const filtered = localReviews.filter((r: any) => !serverIds.includes(r.id));
            if (filtered.length !== localReviews.length) {
              if (filtered.length === 0) localStorage.removeItem(key);
              else localStorage.setItem(key, JSON.stringify(filtered));
            }
          } catch(e) {}
        }
      }
    }

    return { ...responseData, content: transformedContent };
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

  const data = response.data;

  // [수정] 카페 리뷰 리스트의 이미지 요소에 BaseURL 결합 처리
  const baseUrl = (process.env.NEXT_PUBLIC_CLOUDFRONT_URL || '').replace(/\/$/, '');

  const formatImageUrl = (url: string | null | undefined) => {
    if (!url) return url;
    if (url.startsWith('http') || url.startsWith('blob:')) return url;
    const cleanUrl = url.startsWith('/') ? url.slice(1) : url;
    return `${baseUrl}/${cleanUrl}`;
  };

  if (data && Array.isArray(data.content)) {
    data.content = data.content.map((review) => {
      if (Array.isArray(review.images) && review.images.length > 0) {
        review.images = review.images.map((img) => ({
          ...img,
          imageUrl: formatImageUrl(img.imageUrl) as string,
        }));
      }
      return review;
    });

    // [추가/수정] 카페의 서버 리뷰 목록을 성공적으로 받아왔다면, 이 카페의 로컬 리뷰 중복 데이터 제거
    if (typeof window !== 'undefined') {
      const serverIds = data.content.map(r => r.reviewId);
      const key = `cafeReviews-${cafeId}`;
      try {
        const rawData = localStorage.getItem(key);
        if (rawData) {
          const localReviews = JSON.parse(rawData);
          const filteredReviews = localReviews.filter((r: any) => !serverIds.includes(r.id));
          if (filteredReviews.length !== localReviews.length) {
            if (filteredReviews.length === 0) {
              localStorage.removeItem(key);
            } else {
              localStorage.setItem(key, JSON.stringify(filteredReviews));
            }
          }
        }
      } catch(e) {}
    }
  }

  return data; // 서버 응답에서 실제 데이터(content, hasNext, page)만 추출하여 반환
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
      headers: { 'Content-Type': 'multipart/form-data' }, // 파일 업로드를 위한 헤더 설정
    }
  )) as unknown as BaseResponse<PostReviewResponse>;

  // [추가/수정] 리뷰 작성 서버 API 등록 성공 시, 작성 중이던 모든 로컬 임시 데이터 즉시 무조건 소거
  if (typeof window !== 'undefined') {
    localStorage.removeItem(`cafeReviews-${cafeId}`);
    localStorage.removeItem('cafeReviews-mock');
  }

  return response.data; // 등록된 리뷰 상세 데이터(reviewId 포함)를 반환
};

// 리뷰 상세 데이터를 조회하는 함수입니다.
export const getReviewDetail = async (reviewId: string): Promise<ReviewDetailResponse> => {
  const response = (await axios_instance.get<BaseResponse<ReviewDetailResponse>>(
    `/api/reviews/${reviewId}`
  )) as unknown as BaseResponse<ReviewDetailResponse>;

  const data = response.data;

  // [수정] 로버스트한 이미지 경로 포매팅 적용 (이중 슬래시 방지 및 단일 결합 보장)
  const baseUrl = (process.env.NEXT_PUBLIC_CLOUDFRONT_URL || '').replace(/\/$/, '');

  const formatImageUrl = (url: string | null | undefined) => {
    if (!url) return url;
    if (url.startsWith('http') || url.startsWith('blob:')) return url;
    const cleanUrl = url.startsWith('/') ? url.slice(1) : url;
    return `${baseUrl}/${cleanUrl}`;
  };

  if (data) {
    if (Array.isArray(data.imageUrls) && data.imageUrls.length > 0) {
      data.imageUrls = data.imageUrls.map((url) => formatImageUrl(url) as string);
    }

    if (data.cafeThumbnailImage) {
      data.cafeThumbnailImage = formatImageUrl(data.cafeThumbnailImage);
    }
  }

  // [추가/수정] 상세 데이터를 서버에서 정상적으로 불러왔다면, 로컬의 유령 데이터 즉시 소거
  if (typeof window !== 'undefined' && data && data.reviewId) {
    for (let index = 0; index < localStorage.length; index += 1) {
      const key = localStorage.key(index);
      if (key && key.startsWith('cafeReviews-')) {
        try {
          const rawData = localStorage.getItem(key);
          const localReviews = rawData ? JSON.parse(rawData) : [];
          const filteredReviews = localReviews.filter((r: any) => r.id !== data.reviewId);
          if (filteredReviews.length !== localReviews.length) {
            if (filteredReviews.length === 0) {
              localStorage.removeItem(key);
            } else {
              localStorage.setItem(key, JSON.stringify(filteredReviews));
            }
          }
        } catch (e) {}
      }
    }
  }

  return data;
};

// [추가] 선택한 리뷰를 영구 삭제하는 API 함수입니다.
export const deleteReview = async (reviewId: string): Promise<BaseResponse<null>> => {
  const response = (await axios_instance.delete<BaseResponse<null>>(
    `/api/reviews/${reviewId}`
  )) as unknown as BaseResponse<null>;

  // [추가/수정] 리뷰 삭제 서버 API 성공 시, 전역적으로 로컬 스토리지 데이터 완전 소거
  if (typeof window !== 'undefined') {
    for (let index = 0; index < localStorage.length; index += 1) {
      const key = localStorage.key(index);
      if (key && key.startsWith('cafeReviews-')) {
        try {
          const rawData = localStorage.getItem(key);
          const localReviews = rawData ? JSON.parse(rawData) : [];
          const filteredReviews = localReviews.filter((r: any) => r.id !== reviewId);
          if (filteredReviews.length !== localReviews.length) {
            if (filteredReviews.length === 0) {
              localStorage.removeItem(key);
            } else {
              localStorage.setItem(key, JSON.stringify(filteredReviews));
            }
          }
        } catch (e) {}
      }
    }
  }

  return response;
};

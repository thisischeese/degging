import { axios_instance } from "@/api/axios_instance";
import { ApiResponse, MyReviewsResponse,Review } from "../types";

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
  // 1. 실제 서버가 없을 때를 대비한 Mock 데이터 생성 (any 키워드 배제)
  const mockContent: Review[] = [
    {
      reviewId: "eed475e0-424d-4ae4-ac49-cc2e1119d167",
      rating: 5,
      content: "카페가 정말 예뻐요!~~~~~~~~",
      createdAt: "2026-03-12T17:12:49.718464",
      updatedAt: "2026-03-12T17:12:49.718464",
      nickname: "김싸피",
      images: [
        // [수정] 가짜 S3 주소 대신 로컬 이미지 경로 사용
        { imageId: "1", imageUrl: "/images/cafe/cafe1.png" }, 
        { imageId: "2", imageUrl: "/images/cafe/cafe2.png" }
      ],
      cafeName: "아우어베이커리 역삼점" // 옵셔널 필드 활용
    },
    {
      reviewId: "81068c41-597d-4d78-b5da-d42f84061945",
      rating: 3,
      content: "수정이요~~",
      createdAt: "2026-03-11T12:47:31.777753",
      updatedAt: "2026-03-12T17:30:14.479359",
      nickname: "김싸피",
      images: [
        // [수정] 가짜 S3 주소 대신 로컬 이미지 경로 사용
        { imageId: "1", imageUrl: "/images/cafe/cafe2.png" }
      ]
    }
  ];

  const mockResponse: MyReviewsResponse = {
    content: mockContent,
    pageable: {
      pageNumber: page,
      pageSize: size,
      sort: { empty: false, sorted: true, unsorted: false },
      offset: page * size,
      unpaged: false,
      paged: true
    },
    size: size,
    number: page,
    sort: { empty: false, sorted: true, unsorted: false },
    first: page === 0,
    last: true,
    numberOfElements: mockContent.length,
    empty: mockContent.length === 0
  };

  // 2. 서버 통신 로직 (네트워크 에러 시 Mock 데이터 반환하도록 try-catch 구성)
  try {
    const params: Record<string, string | number> = { page, size };
    if (startDate) params.startDate = startDate;
    if (endDate) params.endDate = endDate;

    // 제네릭에 ApiResponse<MyReviewsResponse>를 넣습니다.
    // 인터셉터 덕분에 response 변수는 이미 { status, data, ... } 형태의 객체입니다.
    // Axios 라이브러리의 타입 추론 한계 때문에, 인터셉터 결과를 반영하려면 'as unknown as ...' 처리가 필요할 수 있습니다.
    const response = await axios_instance.get<ApiResponse<MyReviewsResponse>>("/api/reviews/mine", {
      params,
    }) as unknown as ApiResponse<MyReviewsResponse>;
    
    return response.data; // 백엔드 JSON 구조의 'data' 필드를 반환
  } catch (error) {
    console.warn("서버 연결 실패: Mock 데이터를 사용합니다.", error);
    return mockResponse;
  }
};
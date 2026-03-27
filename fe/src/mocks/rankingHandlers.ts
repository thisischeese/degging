import { http, HttpResponse } from 'msw';

const API_BASE_URL = 'http://localhost:8080';

const MOCK_RANKINGS = [
  { id: 1, rank: 1, keyword: "두쫀쿠" },
  { id: 2, rank: 2, keyword: "소금빵" },
  { id: 3, rank: 3, keyword: "붕어빵" },
  { id: 4, rank: 4, keyword: "마카롱" },
  { id: 5, rank: 5, keyword: "휘낭시에" },
  { id: 6, rank: 6, keyword: "케이크" },
  { id: 7, rank: 7, keyword: "쫀득빵" },
  { id: 8, rank: 8, keyword: "푸딩" },
  { id: 9, rank: 9, keyword: "타코야끼" },
  { id: 10, rank: 10, keyword: "에그타르트" },
  { id: 11, rank: 11, keyword: "마들렌" },
  { id: 12, rank: 12, keyword: "파지약과" },
  { id: 13, rank: 13, keyword: "스콘" },
  { id: 14, rank: 14, keyword: "도넛" },
  { id: 15, rank: 15, keyword: "티라미수" },
  { id: 16, rank: 16, keyword: "요거트 아이스크림" },
  { id: 17, rank: 17, keyword: "와플" },
  { id: 18, rank: 18, keyword: "베이글" },
  { id: 19, rank: 19, keyword: "단팥빵" },
  { id: 20, rank: 20, keyword: "크로플" }
];

export const rankingHandlers = [
  // 실시간 디저트 랭킹 조회
  http.get(`${API_BASE_URL}/api/ranks/desserts`, () => {
    return HttpResponse.json({
      status: "success",
      code: 200,
      message: "요청이 성공적으로 처리되었습니다.",
      data: {
        rankings: MOCK_RANKINGS.slice(0, 5), // 실시간 랭킹은 5개만 반환
      }
    });
  }),

  // 온보딩 페이지 애착메뉴 조회
  http.get(`${API_BASE_URL}/api/ranks/desserts/onboarding`, () => {
    return HttpResponse.json({
      status: "success",
      code: 200,
      message: "요청이 성공적으로 처리되었습니다.",
      data: {
        rankings: MOCK_RANKINGS, // 온보딩용은 상위 20개 반환
      }
    });
  }),
];

import { http, HttpResponse } from 'msw';

const API_BASE_URL = 'http://localhost:8080';

const MOCK_RANKINGS = [
  { rank: 1, keyword: "두쫀쿠" },
  { rank: 2, keyword: "소금빵" },
  { rank: 3, keyword: "붕어빵" },
  { rank: 4, keyword: "마카롱" },
  { rank: 5, keyword: "휘낭시에" },
  { rank: 6, keyword: "케이크" },
  { rank: 7, keyword: "쫀득빵" },
  { rank: 8, keyword: "푸딩" },
  { rank: 9, keyword: "타코야끼" },
  { rank: 10, keyword: "에그타르트" },
  { rank: 11, keyword: "마들렌" },
  { rank: 12, keyword: "파지약과" },
  { rank: 13, keyword: "스콘" },
  { rank: 14, keyword: "도넛" },
  { rank: 15, keyword: "티라미수" },
  { rank: 16, keyword: "요거트 아이스크림" },
  { rank: 17, keyword: "와플" },
  { rank: 18, keyword: "베이글" },
  { rank: 19, keyword: "단팥빵" },
  { rank: 20, keyword: "크로플" }
];

export const rankingHandlers = [
  // 실시간 디저트 랭킹 조회
  http.get(`${API_BASE_URL}/api/ranks/desserts`, () => {
    return HttpResponse.json({
      status: "success",
      code: "200",
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
      code: "200",
      message: "요청이 성공적으로 처리되었습니다.",
      data: {
        rankings: MOCK_RANKINGS, // 온보딩용은 상위 20개 반환
      }
    });
  }),
];

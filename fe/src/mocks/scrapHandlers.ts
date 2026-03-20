import { http, HttpResponse } from 'msw';

const MOCK_SCRAPS = [
  {
    scrapId: null,
    name: "모든 스크랩",
    thumbnailUrl: [],
    color: null
  },
  {
    scrapId: "dfd02c92-be16-44b1-a76a-aaed7cb24052",
    name: "역삼역 근처",
    thumbnailUrl: ["https://picsum.photos/seed/cafe1/400/300"],
    color: "RED"
  },
  {
    scrapId: "e2f3c4d5-a1b2-c3d4-e5f6-a7b8c9d0e1f2",
    name: "연남 분좋카 투어",
    thumbnailUrl: [],
    color: "PINK"
  }
];

const MOCK_DETAIL = {
  scrapId: "dfd02c92-be16-44b1-a76a-aaed7cb24052",
  name: "역삼역 근처",
  color: "RED",
  cafes: [
    {
      cafeId: "a2f33c58-d54f-4976-b507-95a9bf255540",
      name: "스타벅스 강남R점",
      cafeIntro: "강남역 리저브 매장"
    }
  ],
  thumbnailUrls: [
    "https://picsum.photos/seed/cafe1/400/300"
  ]
};

export const scrapHandlers = [
  // 1. 카페 스크랩 추가
  http.post('/api/scraps/:scrapId/cafes/:cafeId', () => {
    return HttpResponse.json({
      status: "success",
      code: "200",
      message: "요청이 성공적으로 처리되었습니다.",
      data: null
    });
  }),

  // 2. 카페 스크랩 취소
  http.delete('/api/scraps/:scrapId/cafes/:cafeId', () => {
    return HttpResponse.json({
      status: "success",
      code: "200",
      message: "요청이 성공적으로 처리되었습니다.",
      data: null
    });
  }),

  // 3. 카테고리 생성
  http.post('/api/scraps', () => {
    return HttpResponse.json({
      status: "success",
      code: "200",
      message: "요청이 성공적으로 처리되었습니다.",
      data: null
    });
  }),

  // 4. 카테고리 리스트 조회
  http.get('/api/scraps', () => {
    return HttpResponse.json({
      status: "success",
      code: "200",
      message: "요청이 성공적으로 처리되었습니다.",
      data: MOCK_SCRAPS
    });
  }),

  // 5. 카테고리 상세 조회
  http.get('/api/scraps/:scrapId', () => {
    return HttpResponse.json({
      status: "success",
      code: "200",
      message: "요청이 성공적으로 처리되었습니다.",
      data: MOCK_DETAIL
    });
  }),

  // 6. 카테고리 수정
  http.patch('/api/scraps/:scrapId', () => {
    return HttpResponse.json({
      status: "success",
      code: "200",
      message: "요청이 성공적으로 처리되었습니다.",
      data: null
    });
  }),

  // 7. 카테고리 삭제
  http.delete('/api/scraps/:scrapId', () => {
    return HttpResponse.json({
      status: "success",
      code: "200",
      message: "요청이 성공적으로 처리되었습니다.",
      data: null
    });
  }),

  // 8. 카테고리 추천 (공유 링크 생성)
  http.post('/api/scraps/:scrapId/share-links', () => {
    return HttpResponse.json({
      status: "success",
      code: "200",
      message: "요청이 성공적으로 처리되었습니다.",
      data: {
        shareLink: "https://degging.com/shared/185584bf55e94ade9476f1c4996e0305"
      }
    });
  }),
];

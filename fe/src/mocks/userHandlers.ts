import { http, HttpResponse } from 'msw';

// 백엔드 API 기본 주소를 변수로 뺍니다 (또는 process.env.NEXT_PUBLIC_API_URL 활용 가능)
const API_BASE_URL = 'http://localhost:8080';

export const userHandlers = [
  // 1. 사용자 비밀번호 변경 (User 단)
  http.patch(`${API_BASE_URL}/api/users/password`, async () => {
    return HttpResponse.json({
      code: 200,
      message: '요청에 성공하였습니다.',
      data: null,
    }, { status: 200 });
  }),

  // 2. 사용자 정보 조회
  http.get(`${API_BASE_URL}/api/users`, async () => {
    return HttpResponse.json({
      code: 200,
      message: '요청에 성공하였습니다.',
      data: {
        id: 1,
        email: "user@example.com",
        name: "김다희",
        nickname: "와아앙",
        profileImgUrl: "/images/auth/welcome.png", // 로컬 이미지 경로로 변경하여 Next.js 도메인 에러 방지
        birthDate: "1998.05.20", 
        gender: "FEMALE", 
        tags: ["힙한", "조용한", "차분한"],
        reviewCount: 15
      },
    }, { status: 200 });
  }),

  // 3. 사용자 정보 수정
  http.patch(`${API_BASE_URL}/api/users`, async () => {
    return HttpResponse.json({
      code: 200,
      message: '요청에 성공하였습니다.',
      data: null,
    }, { status: 200 });
  }),

  // 4. 사용자 정보 삭제
  http.delete(`${API_BASE_URL}/api/users`, async () => {
    return HttpResponse.json({
      code: 200,
      message: '요청에 성공하였습니다.',
      data: null,
    }, { status: 200 });
  }),

  // 5. A/B 테스트 전환
  http.get(`${API_BASE_URL}/api/ab-tests/join`, async () => {
    return HttpResponse.json({
      code: 200,
      message: '요청에 성공하였습니다.',
      data: {
        group: "A"
      },
    }, { status: 200 });
  }),
];

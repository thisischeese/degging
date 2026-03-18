import { http, HttpResponse } from 'msw';

// 백엔드 API 기본 주소를 변수로 뺍니다 (또는 process.env.NEXT_PUBLIC_API_URL 활용 가능)
const API_BASE_URL = 'http://localhost:8080';

export const authHandlers = [

  // 1. 회원가입 (Signup)
  http.post(`${API_BASE_URL}/api/auth/signup`, async () => {
    return HttpResponse.json({
      code: 200,
      message: '요청에 성공하였습니다.',
      data: null,
    }, { status: 200 });
  }),

  // 2. 이메일 인증 코드 발송
  http.post(`${API_BASE_URL}/api/auth/email/verification/request`, async () => {
    return HttpResponse.json({
      code: 200,
      message: '요청에 성공하였습니다.',
      data: null,
    }, { status: 200 });
  }),

  // 3. 이메일 인증 코드 확인
  http.post(`${API_BASE_URL}/api/auth/email/verification/confirm`, async () => {
    return HttpResponse.json({
      code: 200,
      message: '요청에 성공하였습니다.',
      data: null,
    }, { status: 200 });
  }),

  // 4. 로그인 (Login)
  http.post(`${API_BASE_URL}/api/auth/login`, async () => {
    return HttpResponse.json({
      code: 200,
      message: '요청에 성공하였습니다.',
      data: {
        accessToken: 'mocked-jwt-access-token',
        refreshToken: 'mocked-jwt-refresh-token',
      },
    }, { status: 200 });
  }),

  // 5. 로그아웃
  http.post(`${API_BASE_URL}/api/auth/logout`, async () => {
    return HttpResponse.json({
      code: 200,
      message: '요청에 성공하였습니다.',
      data: null,
    }, { status: 200 });
  }),

  // 6. 사용자 액세스 토큰 재발급 (Reissue)
  http.post(`${API_BASE_URL}/api/auth/reissue`, async () => {
    return HttpResponse.json({
      code: 200,
      message: '요청에 성공하였습니다.',
      data: null,
    }, { status: 200 });
  }),

  // 7. 비밀번호 찾기 (이메일로 임시비번)
  http.post(`${API_BASE_URL}/api/auth/password/find`, async () => {
    return HttpResponse.json({
      code: 200,
      message: '요청에 성공하였습니다.',
      data: null,
    }, { status: 200 });
  }),

  // 8. 비밀번호 변경 (Auth 단)
  http.patch(`${API_BASE_URL}/api/auth/password/reset`, async () => {
    return HttpResponse.json({
      code: 200,
      message: '요청에 성공하였습니다.',
      data: null,
    }, { status: 200 });
  }),
];


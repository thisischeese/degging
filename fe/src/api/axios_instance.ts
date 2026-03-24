import axios from 'axios';
import Cookies from 'js-cookie';

// 1. 기본 설정 (baseURL은 나중에 .env 파일에서 관리하세요)
export const axios_instance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080', // baseURL -> base_url (단, axios 내부 설정에 따라 baseURL 유지 필요할 수도 있음)
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 2. 요청 인터셉터 (토큰 자동 주입)
axios_instance.interceptors.request.use(
  (config) => {
    const access_token = typeof window !== 'undefined' ? sessionStorage.getItem('access_token') : null;
    const onboarding_token = typeof window !== 'undefined' ? sessionStorage.getItem('ONBOARDING_TOKEN') : null;
    
    const token = access_token || onboarding_token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

import { AxiosError } from 'axios';

// 3. 토큰 갱신 플래그 및 대기열 (여러 요청이 동시에 401을 낼 때 중복 갱신 방지)
let isRefreshing = false;
let failedQueue: Array<{ resolve: (token: string) => void; reject: (error: AxiosError | null) => void }> = [];

const processQueue = (error: AxiosError | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token as string);
    }
  });
  failedQueue = [];
};

// 4. 응답 인터셉터 (언래핑 + 고도화된 에러 처리 + Refresh Token 로직)
axios_instance.interceptors.response.use(
  // [언래핑] 컴포넌트에서는 .data를 쓸 필요 없이 바로 결과값을 받게 됩니다.
  (response) => response.data,
  async (error) => {
    const originalRequest = error.config;

    // 401: 인증 만료 에러 처리 (단, 재시도 했던 요청이 아니어야 함)
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // 이미 다른 요청이 토큰을 갱신 중이라면, 갱신이 끝날 때까지 대기열에 넣음
        return new Promise(function (resolve, reject) {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return axios_instance(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true; // 무한 루프 방지용 플래그
      isRefreshing = true;

      try {
        // [백엔드 연동 포인트] 실제 Refresh Token 재발급 API 주소로 변경 필요
        // 보통 Refresh Token은 HTTP Only 쿠키로 주고받으므로, withCredentials: true 세팅이 필요할 수 있습니다.
        const response = await axios.post(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'}/api/auth/reissue`,
          {},
          { withCredentials: true } 
        );

        // 갱신 성공! 새 토큰 저장
        const newAccessToken = response.data.data.accessToken; // 백엔드 응답 형태에 따라 수정 필요
        sessionStorage.setItem('access_token', newAccessToken);

        // 쿠키도 함께 갱신
        Cookies.set("access_token", newAccessToken, { 
          // expires: 7, 
          path: "/",
          secure: process.env.NODE_ENV === "production",
          sameSite: "Lax"
        });

        // 대기열에 있던 기존 요청들에게 새 토큰 투척
        processQueue(null, newAccessToken);
        isRefreshing = false;

        // 실패했던 원래 요청에 새 토큰을 끼워서 다시 쏘기
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return axios_instance(originalRequest);
        
      } catch (refreshError) {
        // Refresh Token마저도 만료되었거나 갱신 실패 시 -> 진짜 로그아웃 처리
        processQueue(refreshError as AxiosError, null);
        isRefreshing = false;

        alert('세션이 완전히 만료되었습니다. 다시 로그인해주세요.');
        if (typeof window !== 'undefined') {
          sessionStorage.removeItem('access_token');
          Cookies.remove("access_token", { path: "/" }); // 쿠키도 제거
          window.location.href = '/login'; // 로그인 페이지로 이동
        }
        return Promise.reject(refreshError);
      }
    }

    // 403: 권한 없음 (예: 일반 유저가 관리자 페이지 접근)
    if (error.response?.status === 403) {
      alert('접근 권한이 없습니다.');
    }

    return Promise.reject(error);
  }
);
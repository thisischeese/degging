import axios from 'axios';

// 1. 기본 설정 (baseURL은 나중에 .env 파일에서 관리하세요)
export const axiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080',
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 2. 요청 인터셉터 (토큰 자동 주입)
axiosInstance.interceptors.request.use(
  (config) => {
    // 로컬 스토리지나 Zustand 등에서 토큰을 가져옵니다.
    const token = typeof window !== 'undefined' ? localStorage.getItem('accessToken') : null;
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`; // 헤더에 토큰 주입!
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 3. 응답 인터셉터 (에러 공통 처리)
axiosInstance.interceptors.response.use(
  (response) => response.data, // 데이터를 response.data.data까지 안 가도 되게 한 단계 줄여줍니다.
  (error) => {
    // 401 에러(로그인 만료) 시 로그인 페이지로 이동시키는 등의 로직을 넣습니다.
    if (error.response?.status === 401) {
      console.error('로그인이 만료되었습니다.');
    }
    return Promise.reject(error);
  }
);
import axios from 'axios';

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
    const access_token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    
    if (access_token) {
      config.headers.Authorization = `Bearer ${access_token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 3. 응답 인터셉터 (에러 공통 처리)
axios_instance.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      console.error('로그인이 만료되었습니다.');
    }
    return Promise.reject(error);
  }
);
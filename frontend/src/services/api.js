import axios from 'axios';

// API 기본 URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

console.log('🔍 api.js - API_URL:', API_URL);
console.log('🔍 api.js - baseURL will be:', API_URL);


// Axios 인스턴스 생성
const api = axios.create({
  baseURL: API_URL,
  // withCredentials: true, // ← 제거 (더 이상 쿠키 방식 아님)
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 - Authorization 헤더 추가
api.interceptors.request.use(
  (config) => {
    // 🔥 중요: localStorage에서 session_id를 가져와서 헤더에 추가
    const sessionId = localStorage.getItem('session_id');
    if (sessionId) {
      config.headers.Authorization = `Bearer ${sessionId}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // 401 에러 시 localStorage 정리하고 로그인 페이지로 리다이렉트
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('session_id'); // 세션 정리
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
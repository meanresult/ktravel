import api from './api';

const authService = {
  // 회원가입
  signup: async (userData) => {
    try {
      const response = await api.post('/api/auth/signup', userData);
      return response.data;
    } catch (error) {
      throw error.response?.data?.detail || '회원가입 실패';
    }
  },

  // 로그인 (아이디 기반) - session_id 저장 추가
  login: async (username, password) => {
    try {
      const response = await api.post('/api/auth/login', { username, password });
      
      // 🔥 중요: session_id를 localStorage에 저장
      if (response.data.session_id) {
        localStorage.setItem('session_id', response.data.session_id);
      }
      
      return response.data;
    } catch (error) {
      throw error.response?.data?.detail || '로그인 실패';
    }
  },

  // 로그아웃 - session_id 제거 추가
  logout: async () => {
    try {
      const response = await api.post('/api/auth/logout');
      
      // 🔥 중요: localStorage에서 session_id 제거
      localStorage.removeItem('session_id');
      
      return response.data;
    } catch (error) {
      localStorage.removeItem('session_id'); // 에러가 나도 제거
      throw error.response?.data?.detail || '로그아웃 실패';
    }
  },

  // 현재 사용자 정보
  getMe: async () => {
    try {
      const response = await api.get('/api/auth/me');
      return response.data;
    } catch (error) {
      throw error.response?.data?.detail || '사용자 정보 조회 실패';
    }
  },
};

export default authService;
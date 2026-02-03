import api from './api';

const destinationService = {
  // 여행지 목록 조회
  getDestinations: async (limit = 100) => {
    try {
      const response = await api.get('/api/destinations', {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      throw error.response?.data?.detail || '여행지 조회 실패';
    }
  },

  // 여행지 통계
  getStats: async () => {
    try {
      const response = await api.get('/api/destinations/stats');
      return response.data;
    } catch (error) {
      throw error.response?.data?.detail || '통계 조회 실패';
    }
  },

  // 여행지 삭제
  deleteDestination: async (destinationId) => {
    try {
      const response = await api.delete(`/api/destinations/${destinationId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data?.detail || '여행지 삭제 실패';
    }
  },
};

export default destinationService;

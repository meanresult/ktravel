// frontend/src/services/recommendLlmService.js

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export async function getLlmEnhancedRecommendations({
  userId,
  placeType = null,
  topKPerBookmark = 5,
  useLlm = false,
} = {}) {
  if (!userId) {
    throw new Error('userId가 필요합니다.');
  }

  try {
    // ✅ 모든 값을 명시적으로 숫자로 변환
    const requestBody = {
      user_id: parseInt(userId, 10),
      place_type: placeType !== null ? parseInt(placeType, 10) : null,
      top_k_per_bookmark: parseInt(topKPerBookmark, 10),
      created_at: new Date().toISOString(),
    };

    console.log('📤 LLM 추천 요청:', requestBody);
    console.log('🔧 use_llm:', useLlm);

    const token = localStorage.getItem('session_id');
    
    const response = await fetch(
      `${API_URL}/api/recommend-llm/enhanced?use_llm=${useLlm}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
        },
        body: JSON.stringify(requestBody),
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ API 에러 응답:', response.status, errorText);
      throw new Error(`추천 실패 (${response.status}): ${errorText}`);
    }

    const data = await response.json();
    console.log('✅ LLM 추천 응답:', data);

    return data;
  } catch (error) {
    console.error('❌ LLM 추천 API 호출 실패:', error);
    throw new Error(error.message || 'LLM 추천을 가져오는 데 실패했습니다.');
  }
}
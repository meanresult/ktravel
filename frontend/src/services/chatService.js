import api from './api';

const chatService = {
  // 기존: 일반 메시지 전송
  sendMessage: async (message) => {
    try {
      const response = await api.post('/api/chat/send', { message });
      return response.data;
    } catch (error) {
      throw error.response?.data?.detail || '메시지 전송 실패';
    }
  },

  // 🌊 NEW: Streaming 메시지 전송
  sendMessageStreaming: async (message, callbacks = {}) => {
    const {
      onSearching = () => {},
      onFound = () => {},
      onGenerating = () => {},
      onChunk = () => {},
      onComplete = () => {},
      onError = () => {}
    } = callbacks;

    try {
      // ⚠️ axios 대신 fetch 사용 (Streaming 지원)
      const token = localStorage.getItem('token');
      
      const response = await fetch('http://localhost:8000/api/chat/send/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              switch (data.type) {
                case 'searching':
                case 'random':
                  onSearching(data.message);
                  break;
                  
                case 'found':
                  onFound(data.title, data.result);
                  break;
                  
                case 'generating':
                  onGenerating(data.message);
                  break;
                  
                case 'chunk':
                  // 🌊 실시간 텍스트!
                  onChunk(data.content);
                  break;
                  
                case 'done':
                  // ✅ 완료!
                  onComplete(data);
                  break;
                  
                case 'error':
                  onError(data.message);
                  break;
              }
            } catch (e) {
              console.error('JSON parse error:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Streaming error:', error);
      onError(error.message);
    }
  },

  // 기존: 대화 히스토리 조회
  getHistory: async (limit = 50) => {
    try {
      const response = await api.get('/api/chat/history', {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      throw error.response?.data?.detail || '히스토리 조회 실패';
    }
  },
};

export default chatService;
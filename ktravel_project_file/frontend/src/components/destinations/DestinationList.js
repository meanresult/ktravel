import React, { useState, useEffect } from 'react';
import destinationService from '../../services/destinationService';
import './Destinations.css';

function DestinationList({ refreshTrigger }) {
  const [destinations, setDestinations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // 여행지 목록 로드
  const loadDestinations = async () => {
    try {
      setLoading(true);
      const data = await destinationService.getDestinations();
      setDestinations(data);
      setError('');
    } catch (err) {
      setError('여행지 목록을 불러올 수 없습니다');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDestinations();
  }, [refreshTrigger]);

  // 여행지 삭제
  const handleDelete = async (destinationId) => {
    if (!window.confirm('이 여행지를 삭제하시겠습니까?')) {
      return;
    }

    try {
      await destinationService.deleteDestination(destinationId);
      // 목록 새로고침
      loadDestinations();
    } catch (err) {
      alert('삭제 실패: ' + err);
    }
  };

  if (loading) {
    return (
      <div className="destinations-sidebar">
        <h3>📍 내 여행지</h3>
        <p className="loading-text">로딩 중...</p>
      </div>
    );
  }

  return (
    <div className="destinations-sidebar">
      <h3>📍 내 여행지</h3>
      
      {error && <p className="error-text">{error}</p>}

      {destinations.length === 0 ? (
        <div className="empty-destinations">
          <p>아직 여행지가 없습니다.</p>
          <p className="hint">채팅에서 가고 싶은 곳을 말해보세요!</p>
        </div>
      ) : (
        <div className="destinations-list">
          {destinations.map((dest) => (
            <div key={dest.destination_id} className="destination-item">
              <span className="destination-name">{dest.name}</span>
              <button
                onClick={() => handleDelete(dest.destination_id)}
                className="btn-delete"
                title="삭제"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="destinations-count">
        총 {destinations.length}개의 여행지
      </div>
    </div>
  );
}

export default DestinationList;

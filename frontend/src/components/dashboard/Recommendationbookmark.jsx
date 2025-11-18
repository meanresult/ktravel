// frontend/src/components/dashboard/Recommendationbookmark.jsx

import React, { useState } from 'react';
import { Sparkles } from 'lucide-react';
import KMediaDescription from '../KMedia/KMediaDescription';
import { fetchKContentDetail } from '../KMedia/KMediaCardData';

const RecommendationBookmark = ({ items }) => {
  const [selectedItem, setSelectedItem] = useState(null);

  // ✅ K-Media와 동일한 방식으로 수정
  const handleCardClick = async (item) => {
    console.log('📱 추천 카드 클릭:', item);

    const referenceId = item.id;

    if (!referenceId) {
      console.error('❌ reference_id 없음:', item);
      return;
    }

    try {
      // ✅ K-Media에서 사용하는 fetchKContentDetail 사용
      const data = await fetchKContentDetail(referenceId);
      
      console.log('✅ API 응답:', data);

      // ✅ K-Media와 동일한 매핑 방식
      setSelectedItem(data);
    } catch (error) {
      console.error('❌ 상세 정보 조회 실패:', error);
      alert('상세 정보를 불러올 수 없습니다: ' + error.message);
    }
  };

  return (
    <>
      <div className="dashboard-recent-section">
        <h2 className="dashboard-section-title">
          <Sparkles size={20} color="#3853FF" />
          Recommendations for Your Favorite Content
        </h2>
        <div className="dashboard-recent-grid">
          {items.slice(0, 6).map((item) => (
            <div
              key={item.id}
              className="dashboard-recent-card"
              onClick={() => handleCardClick(item)}
              style={{ cursor: 'pointer' }}
            >
              
              <div className="dashboard-recent-image">
                <img src={item.image} alt={item.title} />
              </div>
              <div className="dashboard-recent-content">
                <div className="dashboard-recent-title">{item.title}</div>
                <div className="dashboard-recent-tags">
                  {item.tags &&
                    item.tags.map((tag, idx) => (
                      <span key={idx} className="dashboard-tag">
                        #{tag}
                      </span>
                    ))}
                </div>
                <div className="dashboard-recent-reason">💡 {item.reason}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedItem && (
        <KMediaDescription
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
          onAddLocation={(item, dayTitle) => {
            console.log('✅ 일정 추가:', item.title, dayTitle);
          }}
        />
      )}
    </>
  );
};

export default RecommendationBookmark;
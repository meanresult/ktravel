// ktravel/frontend/src/components/dashboard/RecommendedSlider.jsx
import React, { useState } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  MapPin,
  Sparkles,
} from 'lucide-react';
import KMediaDescription from '../KMedia/KMediaDescription';
import { fetchKContentDetail } from '../KMedia/KMediaCardData';

const RecommendedSlider = ({ items, currentSlide, onPrev, onNext }) => {
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
      <div className="dashboard-slider-container">
        <div className="dashboard-slider-header">
          <h2 className="dashboard-section-title">
            <Sparkles size={20} color="#3853FF" />
            Recommended Content
          </h2>
          <div className="dashboard-slider-controls">
            <button className="dashboard-slider-btn" onClick={onPrev}>
              <ChevronLeft size={18} />
            </button>
            <button className="dashboard-slider-btn" onClick={onNext}>
              <ChevronRight size={18} />
            </button>
          </div>
        </div>

        <div className="dashboard-slides-wrapper">
          <div
            className="dashboard-slides"
            style={{ transform: `translateX(-${currentSlide * 100}%)` }}
          >
            {items.map((item) => (
              <div
                key={item.id}
                className="dashboard-slide-card"
                onClick={() => handleCardClick(item)}
                style={{ cursor: 'pointer' }}
              >
                <div className="dashboard-slide-image">
                  <img src={item.image} alt={item.title} />
                </div>
                <div className="dashboard-slide-content">
                  <span className="dashboard-category-badge">
                    {item.category}
                  </span>
                  <h3 className="dashboard-slide-title">{item.title}</h3>
                  <div className="dashboard-slide-location">
                    <MapPin size={14} />
                    {item.location}
                  </div>
                  <div className="dashboard-slide-reason">
                    💡 {item.reason}
                  </div>
                  <div className="dashboard-slide-tags">
                    {item.tags.map((tag, idx) => (
                      <span key={idx} className="dashboard-tag">
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
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

export default RecommendedSlider;

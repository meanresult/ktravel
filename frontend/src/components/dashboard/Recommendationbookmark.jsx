// ktravel/frontend/src/components/dashboard/Recommendationbookmark.jsx
import React from 'react';
import { Clock } from 'lucide-react';

const RecommendationBookmark = ({ items }) => {
  return (
    <div className="dashboard-recent-section">
      <h2 className="dashboard-section-title">
        <Clock size={20} color="#3853FF" />
        좋아하는 컨텐츠 추천드려요
      </h2>
      <div className="dashboard-recent-grid">
        {items.map((item) => (
          <div key={item.id} className="dashboard-recent-card">
            <div className="dashboard-recent-image">
              <img src={item.image} alt={item.title} />
            </div>
            <div className="dashboard-recent-content">
              <div className="dashboard-recent-title">{item.title}</div>
              <div className="dashboard-recent-tags">
                {item.tags.map((tag, idx) => (
                  <span key={idx} className="dashboard-tag">
                    #{tag}
                  </span>
                ))}
              </div>
              <div className="dashboard-recent-reason">💭 {item.reason}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecommendationBookmark;
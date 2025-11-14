// ktravel/frontend/src/components/dashboard/RecommendedSlider.jsx
import React from 'react';
import {
  ChevronLeft,
  ChevronRight,
  MapPin,
  Sparkles,
} from 'lucide-react';

const RecommendedSlider = ({ items, currentSlide, onPrev, onNext }) => {
  return (
    <div className="dashboard-slider-container">
      <div className="dashboard-slider-header">
        <h2 className="dashboard-section-title">
          <Sparkles size={20} color="#3853FF" />
          추천 콘텐츠
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
            <div key={item.id} className="dashboard-slide-card">
              <div className="dashboard-slide-image">
                <img src={item.image} alt={item.title} />
              </div>
              <div className="dashboard-slide-content">
                <span className="dashboard-category-badge">{item.category}</span>
                <h3 className="dashboard-slide-title">{item.title}</h3>
                <div className="dashboard-slide-location">
                  <MapPin size={14} />
                  {item.location}
                </div>
                <div className="dashboard-slide-reason">💡 {item.reason}</div>
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
  );
};

export default RecommendedSlider;
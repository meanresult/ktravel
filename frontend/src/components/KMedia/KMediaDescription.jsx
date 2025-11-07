import React from "react";
import "./KMediaDescription.css";

export default function KMediaDescription({ item, onClose, onAddLocation }) {
  if (!item) return null;

  return (
    <div className="kmedia-desc-overlay" onClick={onClose}>
      <div className="kmedia-desc-popup" onClick={(e) => e.stopPropagation()}>

        {/* 닫기 버튼 */}
        <button className="desc-close-btn" onClick={onClose}>✕</button>

        {/* 장소 이미지 */}
        <img 
          src={item.thumbnail} 
          alt={item.title} 
          className="desc-img" 
        />

        {/* 장소 이름 */}
        <h2 className="desc-title">{item.title}</h2>

        {/* 장소 설명 */}
        <p className="desc-description">{item.description}</p>

        {/* 지도 */}
        <div className="desc-map">
          <iframe
            title="location-map"
            width="100%"
            height="100%"
            style={{ border: 0, borderRadius: "12px" }}
            loading="lazy"
            allowFullScreen
            src={`https://www.google.com/maps?q=${item.lat},${item.lng}&z=16&output=embed`}
          ></iframe>
        </div>

        {/* ✅ 장소 추가 버튼 */}
        <button 
          className="desc-add-btn"
          onClick={() => onAddLocation(item)}  
        >
          ➕ 장소 추가하기
        </button>

      </div>
    </div>
  );
}

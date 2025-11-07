import React from "react";
import "./KMediaCard.css";

export default function KMediaCard({ item, onLikeToggle, onCardClick }) {
  const handleLikeClick = (e) => {
    e.stopPropagation(); // 카드 클릭 이벤트 막기
    onLikeToggle(item.id);
  };

  return (
    <div className="kmedia-card" onClick={() => onCardClick(item.id)}>
      <img src={item.image} alt={item.title} className="kmedia-image" />
      <h3 className="kmedia-title">{item.title}</h3>
      <p className="kmedia-location">{item.location}</p>

      <button
        className={`kmedia-like-btn ${item.liked ? "liked" : ""}`}
        onClick={handleLikeClick}
      >
        {item.liked ? "❤️" : "🤍"}
      </button>
    </div>
  );
}

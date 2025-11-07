import React, { useState } from "react";
import { mediaMockData } from "../components/KMedia/KMediaCardData";
import KMediaCard from "../components/KMedia/KMediaCard";
import KMediaDescription from "../components/KMedia/KMediaDescription";
import "../styles/KMediaPage.css";

function KMediaPage() {
  const [mediaData, setMediaData] = useState(mediaMockData);
  const [selectedItem, setSelectedItem] = useState(null);

  const handleLikeToggle = (id) => {
    setMediaData((prevData) =>
      prevData.map((item) =>
        item.id === id ? { ...item, liked: !item.liked } : item
      )
    );
  };

  const handleCardClick = (item) => {
    setSelectedItem(item);
  };

  const handlePopupClose = () => {
    setSelectedItem(null);
  };

  // ✅ 장소 추가 기능
  const handleAddLocation = (item) => {
    console.log("Added location:", item);
    alert(`${item.title} 일정에 추가되었습니다! 🎉`);
    setSelectedItem(null);
  };

  return (
    <div className="kmedia-page">
      <div className="kmedia-container">
        <h1 className="kmedia-header-title">K-Media 여행지 추천 🎬</h1>

        <div className="kmedia-grid">
          {mediaData.map((item) => (
            <KMediaCard
              key={item.id}
              item={item}
              onLikeToggle={handleLikeToggle}
              onCardClick={() => handleCardClick(item)}
            />
          ))}
        </div>
      </div>

      {/* ✅ 팝업 활성화 */}
      {selectedItem && (
        <KMediaDescription
          item={selectedItem}
          onClose={handlePopupClose}
          onAddLocation={handleAddLocation} // ✅ 추가
        />
      )}
    </div>
  );
}

export default KMediaPage;

// frontend/src/components/dashboard/BookmarkGrid.jsx

import React, { useState } from 'react';
import { Heart, Filter, SortAsc, Loader2 } from 'lucide-react';
import KMediaDescription from '../KMedia/KMediaDescription';
import { fetchKContentDetail } from '../KMedia/KMediaCardData';
import { PlaceType } from '../../services/bookmarkService';  // ✅ 추가

const BookmarkGrid = ({
  sortedBookmarks,
  isLoadingBookmarks,
  bookmarkError,
  bookmarkFilter,
  sortOption,
  onChangeFilter,
  onChangeSort,
  onRetry,
  onToggleBookmark,
  hoveredCard,
  setHoveredCard,
}) => {
  // ✅ 상세 팝업 상태 추가
  const [selectedItem, setSelectedItem] = useState(null);

  // ✅ 북마크 카드 클릭 핸들러
  const handleBookmarkClick = async (bookmark) => {
    console.log('📱 북마크 카드 클릭:', bookmark);

    // ✅ K-콘텐츠가 아닌 경우는 아직 상세 모달을 열지 않음
  if (bookmark.placeType !== PlaceType.KCONTENT) {
    console.log('ℹ️ 아직 K-콘텐츠 북마크만 상세 보기 지원:', bookmark.placeType);
    return;
  }

    const referenceId = bookmark.referenceId || bookmark.id;

    if (!referenceId) {
      console.error('❌ reference_id 없음:', bookmark);
      return;
    }

    try {
      // ✅ fetchKContentDetail 사용
      const data = await fetchKContentDetail(referenceId);
      
      console.log('✅ API 응답:', data);

      
      setSelectedItem(data);
    } catch (error) {
      console.error('❌ 상세 정보 조회 실패:', error);
      alert('상세 정보를 불러올 수 없습니다: ' + error.message);
    }
  };

  return (
    <>
      <div className="dashboard-bookmark-main">
        <div className="dashboard-bookmark-header">
          <h2 className="dashboard-section-title">
            <Heart size={20} color="#FF6B6B" />
            내 북마크
          </h2>
          <div className="dashboard-bookmark-controls">
            <div className="dashboard-filter-group">
              <span className="dashboard-control-label">
                <Filter size={14} />
                필터
              </span>
              <select
                className="dashboard-control-select"
                value={bookmarkFilter}
                onChange={(e) => onChangeFilter(e.target.value)}
              >
                <option value="전체">전체</option>
                <option value="명소">명소</option>
                <option value="음식">음식</option>
                <option value="K콘텐츠">K콘텐츠</option>
                <option value="페스티벌">페스티벌</option>
              </select>
            </div>
            <div className="dashboard-sort-group">
              <span className="dashboard-control-label">
                <SortAsc size={14} />
                정렬
              </span>
              <select
                className="dashboard-control-select"
                value={sortOption}
                onChange={(e) => onChangeSort(e.target.value)}
              >
                <option value="최신순">최신순</option>
                <option value="오래된순">오래된순</option>
                <option value="이름순">이름순</option>
              </select>
            </div>
          </div>
        </div>

        <div className="dashboard-bookmark-grid">
          {isLoadingBookmarks ? (
            <div className="dashboard-bookmark-loading">
              <Loader2 size={32} className="dashboard-animate-spin" />
              <span style={{ marginLeft: '12px' }}>북마크를 불러오는 중...</span>
            </div>
          ) : bookmarkError && sortedBookmarks.length === 0 ? (
            <div className="dashboard-bookmark-error">
              <div className="dashboard-bookmark-error-title">
                ⚠️ 북마크 조회 실패
              </div>
              <div className="dashboard-bookmark-error-desc">
                {bookmarkError}
              </div>
              <button className="dashboard-retry-button" onClick={onRetry}>
                다시 시도
              </button>
            </div>
          ) : sortedBookmarks.length === 0 ? (
            <div className="dashboard-bookmark-empty">
              <div className="dashboard-bookmark-empty-icon">❤️</div>
              <div className="dashboard-bookmark-empty-title">
                {bookmarkFilter !== '전체'
                  ? `"${bookmarkFilter}" 카테고리에 북마크가 없습니다`
                  : '아직 북마크가 없습니다'}
              </div>
              <div className="dashboard-bookmark-empty-desc">
                마음에 드는 콘텐츠를 저장해보세요
              </div>
            </div>
          ) : (
            sortedBookmarks.map((item) => (
              <div
                key={item.id}
                className="dashboard-bookmark-card"
                onMouseEnter={() => setHoveredCard(item.id)}
                onMouseLeave={() => setHoveredCard(null)}
                onClick={() => handleBookmarkClick(item)} // ✅ 클릭 이벤트
                style={{ cursor: 'pointer' }} // ✅ 커서 변경
              >
                <div className="dashboard-bookmark-image">
                  <img src={item.image} alt={item.title} />
                  <div
                    className="dashboard-bookmark-heart"
                    onClick={(e) => {
                      e.stopPropagation(); // 카드 클릭 방지
                      onToggleBookmark(item.id);
                    }}
                  >
                    <Heart
                      size={16}
                      fill={item.saved ? '#FF6B6B' : 'none'}
                      color="#FF6B6B"
                    />
                  </div>
                  {hoveredCard === item.id && item.actors && (
                    <div className="dashboard-bookmark-hover">
                      출연: {item.actors.join(', ')}
                    </div>
                  )}
                </div>
                <div className="dashboard-bookmark-content">
                  <div className="dashboard-bookmark-title">{item.title}</div>
                  <span className="dashboard-bookmark-category">
                    {item.category}
                  </span>
                  <div className="dashboard-recent-tags">
                    {item.tags.map((tag, idx) => (
                      <span key={idx} className="dashboard-tag">
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* ✅ K-콘텐츠 상세 모달 */}
      {selectedItem && (
        <KMediaDescription
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
          onAddLocation={(item, dayTitle) => {
            console.log('✅ 일정 추가 (북마크 상세에서):', item.title, dayTitle);
          }}
        />
      )}
      </>
    );
  };

export default BookmarkGrid;
// ktravel/frontend/src/components/dashboard/BookmarkGrid.jsx
import React from 'react';
import { Heart, Filter, SortAsc, Loader2 } from 'lucide-react';

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
  return (
    <div className="dashboard-bookmark-main">
      {/* 헤더: 제목 + 필터/정렬 */}
      <div className="dashboard-bookmark-header">
        <h2 className="dashboard-section-title">
          <Heart size={20} color="#FF6B6B" />
          내 북마크
        </h2>
        
        <div className="dashboard-bookmark-controls">
          {/* 필터 */}
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

          {/* 정렬 */}
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

      {/* 북마크 그리드 */}
      <div className="dashboard-bookmark-grid">
        {/* 로딩 상태 */}
        {isLoadingBookmarks && (
          <div className="dashboard-bookmark-loading">
            <Loader2 size={32} className="dashboard-animate-spin" />
            <span style={{ marginLeft: '12px' }}>북마크를 불러오는 중...</span>
          </div>
        )}

        {/* 에러 상태 */}
        {!isLoadingBookmarks && bookmarkError && sortedBookmarks.length === 0 && (
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
        )}

        {/* 빈 상태 */}
        {!isLoadingBookmarks && !bookmarkError && sortedBookmarks.length === 0 && (
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
        )}

        {/* 북마크 카드 리스트 */}
        {!isLoadingBookmarks &&
          sortedBookmarks.map((item) => (
            <div
              key={item.id}
              className="dashboard-bookmark-card"
              onMouseEnter={() => setHoveredCard(item.id)}
              onMouseLeave={() => setHoveredCard(null)}
            >
              {/* 이미지 영역 */}
              <div className="dashboard-bookmark-image">
                <img src={item.image} alt={item.title} />
                
                {/* 하트 버튼 */}
                <div
                  className="dashboard-bookmark-heart"
                  onClick={() => onToggleBookmark(item.id)}
                >
                  <Heart
                    size={16}
                    fill={item.saved ? '#FF6B6B' : 'none'}
                    color="#FF6B6B"
                  />
                </div>

                {/* 호버 시 출연진 표시 */}
                {hoveredCard === item.id && item.actors && (
                  <div className="dashboard-bookmark-hover">
                    출연: {item.actors.join(', ')}
                  </div>
                )}
              </div>

              {/* 카드 내용 */}
              <div className="dashboard-bookmark-content">
                <div className="dashboard-bookmark-title">{item.title}</div>
                <span className="dashboard-bookmark-category">
                  {item.category}
                </span>
                <div className="dashboard-recent-tags">
                  {item.tags &&
                    item.tags.map((tag, idx) => (
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
  );
};

export default BookmarkGrid;
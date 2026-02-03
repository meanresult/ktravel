// components/chat/ChatMessage.js
import React from 'react';
import './Chat.css';

function ChatMessage({ message }) {
    return (
        <div className={`chat-message ${message.isUser ? 'user' : 'bot'} ${message.isError ? 'error' : ''} ${message.isStreaming ? 'streaming' : ''}`}>
            {/* 텍스트 메시지 */}
            <div className="message-text">
                {message.text}
                
                {/* 🌊 Streaming 중일 때 타이핑 커서 표시 */}
                {message.isStreaming && message.text && (
                    <span className="typing-cursor"></span>
                )}
            </div>

            {/* 🔍 검색/생성 상태 표시 */}
            {message.status && (
                <div className="message-status">
                    {message.status}
                </div>
            )}

            {/* 타임스탬프 */}
            <div className="message-timestamp">
                {message.timestamp?.toLocaleTimeString('ko-KR', { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                })}
            </div>

            {/* 🆕 다중 위치 카드 그리드 */}
            {message.locationCards && message.locationCards.length > 0 && (
                <div className="multiple-locations-container">
                    <div className="multiple-locations-header">
                        <h3>🎬 Found {message.totalCount} filming locations!</h3>
                        {message.dramaName && (
                            <p>Drama: {message.dramaName}</p>
                        )}
                    </div>
                    <div className="multiple-locations-grid">
                        {message.locationCards.map((card, idx) => (
                            <div 
                                key={card.content_id || idx}
                                className="location-card-item"
                                onClick={() => window.handleCardClick && window.handleCardClick(card.location_name)}
                                onMouseEnter={() => window.handleCardMouseEnter && window.handleCardMouseEnter(card, 'kcontent')}
                                onMouseLeave={() => window.handleCardMouseLeave && window.handleCardMouseLeave(card, 'kcontent')}
                            >
                                {card.thumbnail && (
                                    <div className="card-image-container">
                                        <img 
                                            src={card.thumbnail}
                                            alt={card.location_name}
                                            className="card-thumbnail"
                                            onError={(e) => {
                                                e.target.style.display = 'none';
                                            }}
                                        />
                                    </div>
                                )}
                                <div className="card-content">
                                    <h4 className="card-title">📍 {card.location_name}</h4>
                                    <p className="card-category">🏷️ {card.category}</p>
                                </div>
                                <div className="card-overlay">
                                    <span>Click for details →</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* 🎯 이미지는 말풍선 완전히 밖으로! */}
            {message.results && message.results.length > 0 && (
                <div className="message-images-below">
                    {message.results.map((result, idx) => (
                        <div 
                            key={idx} 
                            className="image-wrapper-below"
                            onMouseEnter={() => {
                                if (window.handleCardMouseEnter) {
                                    const itemType = result.type;
                                    console.log('🎯 Image card hover:', result, itemType);
                                    window.handleCardMouseEnter(result, itemType);
                                }
                            }}
                            onMouseLeave={() => {
                                if (window.handleCardMouseLeave) {
                                    const itemType = result.type;
                                    window.handleCardMouseLeave(result, itemType);
                                }
                            }}
                        >
                            {/* 🎭 축제 이미지 */}
                            {result.type === 'festival' && result.image_url && (
                                <img 
                                    src={result.image_url}
                                    alt={result.title}
                                    className="content-image-below"
                                    onError={(e) => {
                                        e.target.style.display = 'none';
                                    }}
                                />
                            )}
                            
                            {/* 📍 관광명소 이미지 */}
                            {result.type === 'attraction' && result.image_urls && (
                                <img 
                                    src={Array.isArray(result.image_urls) ? result.image_urls[0] : result.image_urls}
                                    alt={result.title}
                                    className="content-image-below"
                                    onError={(e) => {
                                        e.target.style.display = 'none';
                                    }}
                                />
                            )}
                            
                            {/* 🍽️ 레스토랑 이미지 */}
                            {result.type === 'restaurant' && result.image_url && (
                                <img 
                                    src={result.image_url}
                                    alt={result.restaurant_name || result.title}
                                    className="content-image-below"
                                    onError={(e) => {
                                        e.target.style.display = 'none';
                                    }}
                                />
                            )}

                            {/* 🎬 K-Content(드라마) 이미지 - 필드명 매핑 적용 */}
                            {result.type === 'kcontent' && result.thumbnail && (
                                <img 
                                    src={result.thumbnail}
                                    alt={`${result.drama_name} - ${result.location_name}`}
                                    className="content-image-below"
                                    onError={(e) => {
                                        e.target.style.display = 'none';
                                    }}
                                />
                            )}
                            
                            {/* 이미지 하단 정보 */}
                            <div className="image-caption-below">
                                {/* 🎭 축제 제목 */}
                                {result.type === 'festival' && (
                                    <span className="caption-title-below">{result.title}</span>
                                )}
                                
                                {/* 📍 관광명소 제목 */}
                                {result.type === 'attraction' && (
                                    <span className="caption-title-below">{result.title}</span>
                                )}
                                
                                {/* 🍽️ 레스토랑 제목 */}
                                {result.type === 'restaurant' && (
                                    <span className="caption-title-below">
                                        🍽️ {result.restaurant_name || result.title}
                                    </span>
                                )}

                                {/* 🎬 K-Content 제목 - 필드명 매핑 적용 */}
                                {result.type === 'kcontent' && (
                                    <span className="caption-title-below">
                                        🎬 {result.drama_name} - {result.location_name}
                                    </span>
                                )}
                                
                                {/* 🎭 축제 날짜 */}
                                {result.type === 'festival' && result.start_date && result.end_date && (
                                    <span className="caption-date-below">
                                        📅 {result.start_date} ~ {result.end_date}
                                    </span>
                                )}
                                
                                {/* 📍 관광명소 주소 */}
                                {result.type === 'attraction' && result.address && (
                                    <span className="caption-address-below">
                                        📍 {result.address}
                                    </span>
                                )}
                                
                                {/* 🍽️ 레스토랑 위치 */}
                                {result.type === 'restaurant' && result.place && (
                                    <span className="caption-address-below">
                                        📍 {result.place}
                                    </span>
                                )}
                                
                                {/* 🍽️ 레스토랑 지하철역 */}
                                {result.type === 'restaurant' && result.subway && (
                                    <span className="caption-address-below">
                                        🚇 {result.subway}
                                    </span>
                                )}

                                {/* 🎬 K-Content 주소 - 필드명 매핑 적용 */}
                                {result.type === 'kcontent' && result.address && (
                                    <span className="caption-address-below">
                                        📍 {result.address}
                                    </span>
                                )}

                                {/* 🎬 K-Content 카테고리 - 필드명 매핑 적용 */}
                                {result.type === 'kcontent' && result.category && (
                                    <span className="caption-address-below">
                                        🏷️ {result.category}
                                    </span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* 🎯 기존 개별 타입 표시 (하위 호환성) */}
            
            {/* 축제만 표시 */}
            {!message.results && !message.locationCards && message.festivals && message.festivals.length > 0 && (
                <div className="message-images-below">
                    {message.festivals.map((festival, idx) => (
                        <div 
                            key={idx} 
                            className="image-wrapper-below"
                            onMouseEnter={() => window.handleCardMouseEnter && window.handleCardMouseEnter(festival, 'festival')}
                            onMouseLeave={() => window.handleCardMouseLeave && window.handleCardMouseLeave(festival, 'festival')}
                        >
                            {festival.image_url && (
                                <>
                                    <img 
                                        src={festival.image_url}
                                        alt={festival.title}
                                        className="content-image-below"
                                        onError={(e) => {
                                            e.target.style.display = 'none';
                                        }}
                                    />
                                    <div className="image-caption-below">
                                        <span className="caption-title-below">{festival.title}</span>
                                        {festival.start_date && festival.end_date && (
                                            <span className="caption-date-below">
                                                📅 {festival.start_date} ~ {festival.end_date}
                                            </span>
                                        )}
                                    </div>
                                </>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* K-Content만 표시 (개별 호환성) - 필드명 매핑 적용 */}
            {!message.results && !message.locationCards && message.kcontents && message.kcontents.length > 0 && (
                <div className="message-images-below">
                    {message.kcontents.map((kcontent, idx) => (
                        <div 
                            key={idx} 
                            className="image-wrapper-below"
                            onMouseEnter={() => window.handleCardMouseEnter && window.handleCardMouseEnter(kcontent, 'kcontent')}
                            onMouseLeave={() => window.handleCardMouseLeave && window.handleCardMouseLeave(kcontent, 'kcontent')}
                        >
                            {kcontent.thumbnail && (
                                <>
                                    <img 
                                        src={kcontent.thumbnail}
                                        alt={`${kcontent.drama_name} - ${kcontent.location_name}`}
                                        className="content-image-below"
                                        onError={(e) => {
                                            e.target.style.display = 'none';
                                        }}
                                    />
                                    <div className="image-caption-below">
                                        <span className="caption-title-below">
                                            🎬 {kcontent.drama_name} - {kcontent.location_name}
                                        </span>
                                        {kcontent.address && (
                                            <span className="caption-address-below">
                                                📍 {kcontent.address}
                                            </span>
                                        )}
                                        {kcontent.category && (
                                            <span className="caption-address-below">
                                                🏷️ {kcontent.category}
                                            </span>
                                        )}
                                    </div>
                                </>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* 레스토랑만 표시 (개별 호환성) */}
            {!message.results && !message.locationCards && message.restaurants && message.restaurants.length > 0 && (
                <div className="message-images-below">
                    {message.restaurants.map((restaurant, idx) => (
                        <div 
                            key={idx} 
                            className="image-wrapper-below"
                            onMouseEnter={() => window.handleCardMouseEnter && window.handleCardMouseEnter(restaurant, 'restaurant')}
                            onMouseLeave={() => window.handleCardMouseLeave && window.handleCardMouseLeave(restaurant, 'restaurant')}
                        >
                            {restaurant.image_url && (
                                <>
                                    <img 
                                        src={restaurant.image_url}
                                        alt={restaurant.restaurant_name || restaurant.title}
                                        className="content-image-below"
                                        onError={(e) => {
                                            e.target.style.display = 'none';
                                        }}
                                    />
                                    <div className="image-caption-below">
                                        <span className="caption-title-below">
                                            🍽️ {restaurant.restaurant_name || restaurant.title}
                                        </span>
                                        {restaurant.place && (
                                            <span className="caption-address-below">
                                                📍 {restaurant.place}
                                            </span>
                                        )}
                                        {restaurant.subway && (
                                            <span className="caption-address-below">
                                                🚇 {restaurant.subway}
                                            </span>
                                        )}
                                    </div>
                                </>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default ChatMessage;
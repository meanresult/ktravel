import React, { useState, useEffect, useMemo } from "react";
import {
    fetchShuffledKContentList,
    fetchKContentDetail
} from "../components/KMedia/KMediaCardData";
import KMediaCard from "../components/KMedia/KMediaCard";
import KMediaDescription from "../components/KMedia/KMediaDescription";
import "../styles/KMediaPage.css";
import { addBookmark, deleteBookmark, PlaceType } from '../services/bookmarkService';

const ITEMS_PER_PAGE = 9;
const MAX_BUTTONS = 5;
const PLACE_TYPE_KMEDIA = 3;
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';


const getImageList = (urlList) => urlList;

function KMediaPage() {
    const [mediaData, setMediaData] = useState([]);
    const [userId, setUserId] = useState(null);  // ✅ 추가!
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedItem, setSelectedItem] = useState(null);
    const [searchTerm, setSearchTerm] = useState("");
    const [currentPage, setCurrentPage] = useState(1);

    // ✅ 헬퍼 함수들을 컴포넌트 안에 정의!
    const fetchWithAuth = async (url, options = {}) => {
        const token = localStorage.getItem('session_id');
        if (!token) {
            alert('로그인이 필요합니다!');
            throw new Error('로그인이 필요합니다');
        }

        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            ...(options.headers || {}),
        };

        const res = await fetch(url, { ...options, headers });
        if (!res.ok) {
            const text = await res.text().catch(() => '');
            throw new Error(`API ${res.status}: ${text}`);
        }
        return res.json().catch(() => ({}));
    };

    const getLikedContentIds = async () => {
        if (!userId) {
            console.log('⚠️ 로그인 안 됨');
            return { likedIds: new Set(), bookmarkMap: {} }; // ✅ 변경!
        }
        
        try {
            const token = localStorage.getItem('session_id');
            const response = await fetch(
                `${API_URL}/bookmark/${userId}`,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                }
            );
            
            if (!response.ok) {
                throw new Error('북마크 목록 조회 실패');
            }
            
            const bookmarks = await response.json();
            console.log('📚 전체 북마크:', bookmarks);
            
            // place_type이 3인 것만 필터링
            const kcontentBookmarks = bookmarks.filter(
                b => b.place_type === PLACE_TYPE_KMEDIA
            );
            
            const likedIds = new Set(kcontentBookmarks.map(b => b.reference_id));
            
            // ✅ reference_id → bookmark_id 매핑 추가!
            const bookmarkMap = {};
            kcontentBookmarks.forEach(b => {
                bookmarkMap[b.reference_id] = b.bookmark_id;
            });
            
            console.log('💖 좋아요한 콘텐츠 IDs:', Array.from(likedIds));
            console.log('🗺️ 북마크 ID 맵:', bookmarkMap);
            
            return { likedIds, bookmarkMap }; // ✅ 변경!
            
        } catch (err) {
            console.error('좋아요 목록 조회 실패:', err);
            return { likedIds: new Set(), bookmarkMap: {} }; // ✅ 변경!
        }
    };

    

    // ✅ 초기 데이터 로딩 (좋아요 상태 포함)
    useEffect(() => {
        const getUserId = async () => {
            try {
                const token = localStorage.getItem('session_id');
                if (!token) {
                    console.log('⚠️ 로그인 안 됨');
                    return;
                }
                
                // 사용자 정보 API 호출
                const response = await fetch(`${API_URL}/api/auth/me`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    const userData = await response.json();
                    setUserId(userData.user_id);
                    console.log('✅ 사용자 ID:', userData.user_id);
                }
            } catch (err) {
                console.error('사용자 정보 조회 실패:', err);
            }
        };
        
        getUserId();
    }, []);

    // ✅ 2. 콘텐츠 데이터 로딩 (userId가 준비되면 실행)
    useEffect(() => {
        const loadKContentData = async () => {
            setIsLoading(true);
            try {
                // 1️⃣ 먼저 콘텐츠 데이터만 가져오기
                const data = await fetchShuffledKContentList(0, 9999);
                console.log('📦 콘텐츠 데이터:', data.length, '개');
                
                // 2️⃣ userId가 있으면 좋아요 상태 + bookmarkId 추가
                if (userId) {
                    const { likedIds, bookmarkMap } = await getLikedContentIds(); // ✅ 변경!
                    const dataWithLikedState = data.map(item => ({
                        ...item,
                        liked: likedIds.has(item.id),
                        bookmarkId: bookmarkMap[item.id] || null // ✅ 추가!
                    }));
                    setMediaData(dataWithLikedState);
                } else {
                    // 로그인 안 했으면 liked: false
                    setMediaData(data.map(item => ({ 
                        ...item, 
                        liked: false,
                        bookmarkId: null // ✅ 추가!
                    })));
                }
                
                setError(null);
            } catch (err) {
                console.error("데이터 로드 실패:", err);
                setError("데이터를 불러오는 데 실패했습니다.");
            } finally {
                setIsLoading(false);
            }
        };
        
        if (userId !== null) {
            loadKContentData();
        }
    }, [userId]);


    // ✅ 하트 클릭 핸들러
    const handleLikeToggle = async (id) => {
        console.log('🔥 하트 클릭됨! ID:', id);
        
        const item = mediaData.find(i => i.id === id);
        if (!item) {
            console.error('❌ 아이템을 찾을 수 없습니다:', id);
            return;
        }

        const newLikedState = !item.liked;
        console.log('💖 새 상태:', newLikedState ? '좋아요' : '좋아요 취소');

        // 화면 즉시 반영
        setMediaData(prevData =>
            prevData.map(i =>
                i.id === id ? { ...i, liked: newLikedState } : i
            )
        );

        try {
            if (newLikedState) {
                // ✅ 북마크 추가 (DB 컬럼 구조에 맞게 필드 채우기)
                const result = await addBookmark({
                    userId: userId,
                    name: item.title || item.name,  // 표시용 이름
                    placeType: PlaceType.KCONTENT,   // 3

                    // 🔑 Qdrant / 추천에서 기준이 되는 ID
                    referenceId: item.reference_id || item.id,

                    // ✅ 영어 정보들 (없으면 빈 문자열)
                    locationName: item.location_name_en || item.location_name || "",
                    address: item.address_en || "",
                    category: item.category_en || "",
                    keyword: item.keyword_en || "",
                    tripTipEn: item.trip_tip_en || "",

                    // 위치 정보
                    latitude: item.latitude ?? null,
                    longitude: item.longitude ?? null,

                    // 이미지
                    imageUrl: item.thumbnail || (item.image_url_list?.[0] ?? ""),

                    // 기타
                    notes: null,
                    extractedFromConversId: 0,   // 대화에서 추출한 게 아니면 0
                });

                console.log('✅ K-콘텐츠 북마크 저장 성공!', result);

                // bookmark_id 반영
                setMediaData(prevData =>
                    prevData.map(i =>
                        i.id === id ? { ...i, bookmarkId: result.bookmark_id } : i
                    )
                );
            } else {
                // ✅ 북마크 삭제
                if (!item.bookmarkId) {
                    console.error('❌ bookmarkId가 없습니다!');
                    throw new Error('북마크 ID를 찾을 수 없습니다.');
                }

                await deleteBookmark(item.bookmarkId, userId);
                console.log('✅ 북마크 삭제 성공!');

                setMediaData(prevData =>
                    prevData.map(i =>
                        i.id === id ? { ...i, bookmarkId: null } : i
                    )
                );
            }
        } catch (err) {
            console.error('❌ 저장/삭제 실패:', err);
            alert('처리에 실패했습니다: ' + err.message);

            // 실패 시 화면 상태 되돌리기
            setMediaData(prevData =>
                prevData.map(i =>
                    i.id === id ? { ...i, liked: !newLikedState } : i
                )
            );
        }
    };


    // 필터링된 목록 계산
    const filteredMedia = useMemo(() => {
        if (!searchTerm) return mediaData;
        const lowercasedSearch = searchTerm.toLowerCase();
        return mediaData.filter((item) => {
            const titleMatch = item.title?.toLowerCase().includes(lowercasedSearch);
            const locationMatch = item.location?.toLowerCase().includes(lowercasedSearch);
            return titleMatch || locationMatch;
        });
    }, [mediaData, searchTerm]);

    // 페이지네이션 관련 값 계산
    const { paginatedData, totalPages, displayPageNumbers } = useMemo(() => {
        const totalPages = Math.ceil(filteredMedia.length / ITEMS_PER_PAGE);
        const safeCurrentPage = Math.min(currentPage, totalPages > 0 ? totalPages : 1);
        const indexOfLastItem = safeCurrentPage * ITEMS_PER_PAGE;
        const indexOfFirstItem = indexOfLastItem - ITEMS_PER_PAGE;
        const currentItems = filteredMedia.slice(indexOfFirstItem, indexOfLastItem);

        let startPage = Math.max(1, safeCurrentPage - Math.floor(MAX_BUTTONS / 2));
        if (startPage + MAX_BUTTONS - 1 > totalPages) {
            startPage = Math.max(1, totalPages - MAX_BUTTONS + 1);
        }

        const endPage = Math.min(totalPages, startPage + MAX_BUTTONS - 1);
        const displayPageNumbers = [];
        for (let i = startPage; i <= endPage; i++) displayPageNumbers.push(i);

        return { paginatedData: currentItems, totalPages, displayPageNumbers };
    }, [filteredMedia, currentPage]);

    useEffect(() => {
        if (currentPage > totalPages && totalPages > 0) {
            setCurrentPage(totalPages);
        } else if (filteredMedia.length > 0 && currentPage === 0) {
            setCurrentPage(1);
        }
    }, [totalPages, filteredMedia.length, currentPage]);

    const handlePageChange = (page) => {
        if (page >= 1 && page <= totalPages) {
            setCurrentPage(page);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    };

    const handleSearchChange = (event) => {
        setSearchTerm(event.target.value);
        setCurrentPage(1);
    };

    const handleCardClick = async (item) => {
        try {
            const detailItem = await fetchKContentDetail(item.id);
            setSelectedItem(detailItem);
        } catch (err) {
            console.error("상세 데이터 로드 실패:", err);
            alert("상세 정보를 불러올 수 없습니다.");
        }
    };

    const handlePopupClose = () => setSelectedItem(null);

    const handleAddLocation = async (item, dayTitle) => {
        console.log('✅ KMediaPage - 목적지가 추가되었습니다:', {
            item: item.title,
            dayTitle: dayTitle
        });
        window.dispatchEvent(new CustomEvent('destinationAdded', {
            detail: { dayTitle }
        }));
    };

    if (isLoading)
        return (
            <div className="kmedia-page">
                <h1 className="kmedia-header-title">K-Media Spotlight 🎬</h1>
                <div className="kmedia-loading">데이터를 불러오는 중...</div>
            </div>
        );

    if (error)
        return (
            <div className="kmedia-page">
                <h1 className="kmedia-header-title">K-Media Spotlight 🎬</h1>
                <div className="kmedia-error-message">{error}</div>
            </div>
        );

    return (
        <div className="kmedia-page">
            <div className="kmedia-container">
                <h1 className="kmedia-header-title">K-Media Spotlight 🎬</h1>
                
                <input
                    type="text"
                    placeholder=" 🔎 Search for a title or place"
                    value={searchTerm}
                    onChange={handleSearchChange}
                    className="kmedia-search-input"
                />

                <div className="kmedia-grid">
                    {paginatedData.length > 0 ? (
                        paginatedData.map((item) => {
                            const images = getImageList(item.image_url_list || []);
                            return (
                                <KMediaCard
                                    key={item.id}
                                    item={{
                                        ...item,
                                        thumbnail: item.thumbnail,
                                        second_image: images[1] || item.thumbnail,
                                        third_image: images[2] || null,
                                        image: images
                                    }}
                                    onLikeToggle={handleLikeToggle}
                                    onCardClick={() => handleCardClick(item)}
                                />
                            );
                        })
                    ) : (
                        <p className="kmedia-no-results">
                            "{searchTerm}"에 대한 검색 결과가 없습니다.
                        </p>
                    )}
                </div>
                
                {totalPages > 1 && (
                    <div className="kmedia-pagination">
                        <button 
                            onClick={() => handlePageChange(currentPage - 1)}
                            disabled={currentPage === 1}
                            className="pagination-button"
                        >
                            &lt; Before
                        </button>
                        
                        {displayPageNumbers.map(page => (
                            <button
                                key={page}
                                onClick={() => handlePageChange(page)}
                                disabled={currentPage === page}
                                className={currentPage === page ? "pagination-button active" : "pagination-button"}
                            >
                                {page}
                            </button>
                        ))}
                        
                        <button 
                            onClick={() => handlePageChange(currentPage + 1)}
                            disabled={currentPage === totalPages}
                            className="pagination-button"
                        >
                            Next &gt;
                        </button>
                    </div>
                )}
            </div>

            {selectedItem && (
                <KMediaDescription
                    item={selectedItem}
                    onClose={handlePopupClose}
                    onAddLocation={handleAddLocation}
                />
            )}
        </div>
    );
}

export default KMediaPage;
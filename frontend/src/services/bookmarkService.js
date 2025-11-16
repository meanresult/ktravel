/**
 * 📡 bookmarkService.js
 * 백엔드 북마크 API와 통신하는 서비스 레이어
 */
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_BASE = `${API_URL}/api`;

// ✅ place_type 상수 정의
export const PlaceType = {
    RESTAURANT: 0,  // 음식점
    FESTIVAL: 1,    // 축제
    ATTRACTION: 2,  // 명소
    KCONTENT: 3     // K-콘텐츠
};

/**
 * 🔐 인증 헤더 생성
 */
const getAuthHeaders = () => {
    const token = localStorage.getItem('session_id');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
};

/**
 * 📋 사용자의 모든 북마크 조회
 * @param {number} userId - 사용자 ID
 * @returns {Promise<Array>} 북마크 목록
 */
export const getBookmarks = async (userId) => {
    try {
        console.log('📡 북마크 조회 요청: user_id =', userId);
        
        const response = await fetch(`${API_BASE}/bookmark/${userId}`, {
            method: 'GET',
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('❌ 북마크 조회 실패:', response.status, errorText);
            throw new Error(`북마크 조회 실패: ${response.status}`);
        }

        const bookmarks = await response.json();
        console.log('✅ 북마크 조회 성공:', bookmarks.length, '개');
        
        return bookmarks;
    } catch (error) {
        console.error('❌ 북마크 조회 에러:', error);
        throw error;
    }
};

/**
 * 🔖 북마크 추가 (범용)
 * 
 * @param {Object} options - 북마크 옵션
 * @param {number} options.userId - 사용자 ID
 * @param {string} options.name - 장소명
 * @param {number} options.placeType - 장소 타입 (PlaceType 상수 사용)
 * @param {number} options.referenceId - 원본 콘텐츠 ID
 * @param {string} [options.locationName] - 위치명 (영어)
 * @param {string} [options.address] - 주소 (영어)
 * @param {string} [options.category] - 카테고리 (영어)
 * @param {string} [options.keyword] - 키워드 (영어)
 * @param {string} [options.tripTipEn] - 여행 팁 (영어)
 * @param {number} [options.latitude] - 위도
 * @param {number} [options.longitude] - 경도
 * @param {string} [options.imageUrl] - 이미지 URL
 * @param {string} [options.notes] - 메모
 * @returns {Promise<Object>} 생성된 북마크
 */
export const addBookmark = async ({
    userId,
    name,
    placeType,
    referenceId,
    locationName = null,
    address = null,
    category = null,
    keyword = null,
    tripTipEn = null,
    latitude = null,
    longitude = null,
    imageUrl = null,
    notes = null
}) => {
    try {
        const placeTypeName = Object.keys(PlaceType).find(
            key => PlaceType[key] === placeType
        );
        console.log(`📤 북마크 추가: ${name} (${placeTypeName})`);

        const body = {
            user_id: userId,
            name: name,
            place_type: placeType,
            reference_id: referenceId,
            location_name: locationName,
            address: address,
            category: category,
            keyword: keyword,
            trip_tip_en: tripTipEn,
            latitude: latitude,
            longitude: longitude,
            image_url: imageUrl,
            notes: notes,
            extracted_from_convers_id: 0
        };

        console.log('📤 요청 데이터:', body);

        const response = await fetch(`${API_BASE}/bookmark`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(body)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `북마크 추가 실패: ${response.status}`);
        }

        const result = await response.json();
        console.log('✅ 북마크 추가 성공:', result);
        return result;
    } catch (error) {
        console.error('❌ 북마크 추가 에러:', error);
        throw error;
    }
};

/**
 * 🗑️ 북마크 삭제
 * @param {number} bookmarkId - 북마크 ID
 * @param {number} userId - 사용자 ID
 * @returns {Promise<Object>} 삭제 결과
 */
export const deleteBookmark = async (bookmarkId, userId) => {
    try {
        console.log(`🗑️ 북마크 삭제 요청: bookmark_id=${bookmarkId}, user_id=${userId}`);

        const response = await fetch(
            `${API_BASE}/bookmark/${bookmarkId}/${userId}`,
            {
                method: 'DELETE',
                headers: getAuthHeaders()
            }
        );

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `북마크 삭제 실패: ${response.status}`);
        }

        const result = await response.json();
        console.log('✅ 북마크 삭제 성공:', result);
        return result;
    } catch (error) {
        console.error('❌ 북마크 삭제 에러:', error);
        throw error;
    }
};

/**
 * 📊 추천을 위한 reference_id 목록 조회
 * @param {number} userId - 사용자 ID
 * @param {number} [placeType] - 필터링할 place_type (선택)
 * @returns {Promise<Array>} reference_id 목록
 */
export const getReferenceIds = async (userId, placeType = null) => {
    try {
        let url = `${API_BASE}/bookmark/${userId}/reference-ids`;
        if (placeType !== null) {
            url += `?place_type=${placeType}`;
        }

        const response = await fetch(url, {
            method: 'GET',
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error(`reference_id 조회 실패: ${response.status}`);
        }

        const data = await response.json();
        console.log('✅ reference_id 조회 성공:', data.reference_ids);
        return data.reference_ids;
    } catch (error) {
        console.error('❌ reference_id 조회 에러:', error);
        throw error;
    }
};

/**
 * 👤 사용자 정보 조회
 * @returns {Promise<Object>} 사용자 정보
 */
export const getCurrentUser = async () => {
    try {
        const token = localStorage.getItem('session_id');
        
        if (!token) {
            console.warn('⚠️ 토큰 없음');
            return null;
        }

        const response = await fetch(`${API_BASE}/auth/me`, {
            method: 'GET',
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error(`사용자 정보 조회 실패: ${response.status}`);
        }

        const userData = await response.json();
        console.log('✅ 사용자 정보:', userData);
        
        return {
            id: userData.user_id || userData.id,
            name: userData.name || userData.username,
            email: userData.email,
            profileImg: userData.profile_img || '/images/profile_emily.jpg'
        };
    } catch (error) {
        console.error('❌ 사용자 정보 조회 실패:', error);
        return null;
    }
};
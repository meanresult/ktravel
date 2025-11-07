// src/pages/KPathIdeaPage.jsx

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Search, MapPin, Loader, BusFront, Clock, Wallet, Route, Trash2 } from 'lucide-react';
import '../styles/KPathIdeaPage.css';
import SubPathItem from '../components/kpathidea/SubPathItem';
import { readLat, readLng } from '../components/kpathidea/mapUtils';
import useMapLogic from '../components/kpathidea/useMapLogic';
import MemoModal from '../components/kpathidea/MemoModal'; 

// API 및 환경 변수 설정
const NAVER_MAPS_CLIENT_ID = process.env.REACT_APP_NAVER_MAPS_CLIENT_ID;
const LOCATION_API_URL = "http://127.0.0.1:8000/search/location";
const ROUTE_API_URL = "http://127.0.0.1:8000/api/search/route";
const GOOGLE_API_KEY = process.env.REACT_APP_GOOGLE_API_KEY;

// ⭐ scheduleLocations prop 추가
function KPathIdeaPage({ scheduleLocation, scheduleLocations = [] }) {

    // --- 1. 상태 관리 (useState) ---
    const [routePolyline, setRoutePolyline] = useState(null);
    const [userMarkers, setUserMarkers] = useState([]);
    const [selectedStartId, setSelectedStartId] = useState(null);
    const [selectedEndId, setSelectedEndId] = useState(null);
    const [routeResult, setRouteResult] = useState(null);
    const [isSummaryVisible, setIsSummaryVisible] = useState(false);
    const [isSelectingPath, setIsSelectingPath] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [message, setMessage] = useState('🔍 장소 검색(자동완성 지원) 또는 입력 후 검색 버튼을 사용하세요.');
    const [isDeleteMode, setIsDeleteMode] = useState(false);

    const [markerMemos, setMarkerMemos] = useState({}); 
    const [modalContent, setModalContent] = useState(null); 

    const stateRef = useRef({});
    const fetchRouteRef = useRef(null);
    const deleteListenersRef = useRef({});

    // --- 2. 마커 메모 모달 제어 함수 정의 ---
    const openMemoModal = useCallback((markerData) => {
        const currentMemo = markerMemos[markerData.id] || { 
            title: markerData.name, 
            memo: '',
        }; 
        
        setModalContent({
            markerId: markerData.id,
            initialTitle: currentMemo.title,
            initialMemo: currentMemo.memo,
            onSave: (newTitle, newMemo) => {
                setMarkerMemos(prev => ({
                    ...prev,
                    [markerData.id]: { title: newTitle, memo: newMemo },
                }));
                
                setUserMarkers(prev => prev.map(m => 
                    m.id === markerData.id ? { ...m, name: newTitle } : m
                ));
                
                setModalContent(null);
                setMessage(`📝 마커 '${newTitle}' 정보가 저장되었습니다.`);
            },
            onClose: () => setModalContent(null)
        });
    }, [markerMemos, setMarkerMemos, setUserMarkers]);

    // --- 3. 훅 호출 및 기능 가져오기 (useMapLogic 호출) ---
    const {
        map,
        isApiLoaded,
        clearRoute,
        drawSegmentedPolyline,
        mapObjectsRef, 
        handleDeleteMarker,
    } = useMapLogic(
        NAVER_MAPS_CLIENT_ID,
        setMessage,
        setRouteResult,
        setIsSummaryVisible,
        setRoutePolyline,
        setUserMarkers,
        setSelectedStartId,
        setSelectedEndId,
        stateRef,
        fetchRouteRef,
        openMemoModal,
        markerMemos
    );

    // --- ⭐ 4. scheduleLocations 처리 (일정 선택 시 목적지 로드) ---
    useEffect(() => {
        if (!scheduleLocations || scheduleLocations.length === 0) {
            // 목적지가 없으면 마커 초기화 (옵션)
            // setUserMarkers([]);
            // setMessage('📭 이 일정에는 아직 목적지가 없습니다.');
            return;
        }

        console.log('📍 일정의 목적지들을 마커로 추가:', scheduleLocations);
        
        // ⭐ 기존 검색으로 추가한 마커는 유지하고 싶다면:
        // setUserMarkers(prev => [...prev, ...scheduleLocations]);
        
        // ⭐ 일정의 목적지만 표시하고 싶다면 (권장):
        setUserMarkers(scheduleLocations);
        
        setMessage(`📍 ${scheduleLocations.length} destinations loaded.`);
        
        // 첫 번째 목적지로 지도 중심 이동
        if (map && scheduleLocations[0]) {
            try {
                const firstLocation = scheduleLocations[0];
                map.setCenter(
                    new window.naver.maps.LatLng(
                        firstLocation.lat, 
                        firstLocation.lng
                    )
                );
                map.setZoom(13, true);
                console.log(`🗺️ 지도 중심 이동: ${firstLocation.name}`);
            } catch (e) {
                console.warn('지도 중심 이동 실패', e);
            }
        }
    }, [scheduleLocations, map]);

    // --- 5. 통합 Ref 업데이트 (useEffect) ---
    useEffect(() => {
        stateRef.current = {
            userMarkers,
            selectedStartId,
            selectedEndId,
            routeResult,
            routePolyline,
            isSummaryVisible,
            isSelectingPath,
            isLoading,
            isDeleteMode,
            markerMemos,
        };
    }, [userMarkers, selectedStartId, selectedEndId, routeResult,
        routePolyline, isSummaryVisible, isSelectingPath, isLoading, isDeleteMode, markerMemos]);

    // --- 6. 경로 검색 함수 정의 ---
    const fetchRoute = useCallback(async (startLat, startLng, endLat, endLng) => {
        setIsLoading(true);
        setMessage('🚌 대중교통 경로 검색 중...');
        setRouteResult(null);

        const requestBody = { startLat, startLng, endLat, endLng };

        try {
            const response = await fetch(ROUTE_API_URL, {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(requestBody),
            });

            if (!response.ok) {
                let errorText = `HTTP 오류! 상태 코드: ${response.status}`;
                throw new Error(errorText);
            }
            const data = await response.json();

            const routeData = {
                totalTime: data.totalTime ?? null, fare: data.fare ?? null, subPath: data.subPath ?? [],
            };

            drawSegmentedPolyline(data.segmentedPath ?? [], routeData);

        } catch (error) {
            console.error('경로 검색 중 오류 발생:', error);
            setMessage(`❌ 경로 검색 실패: ${error.message}.`);
            clearRoute();
        } finally {
            setIsLoading(false);
            setIsSelectingPath(false);
        }
    }, [drawSegmentedPolyline, clearRoute]);

    // --- 7. fetchRoute 참조 연결 ---
    useEffect(() => {
        fetchRouteRef.current = fetchRoute;
    }, [fetchRoute]);

    // --- 8. 위치 검색 함수 (마커 추가) ---
    const handleSearch = async (e) => {
        e?.preventDefault?.();
        if (!searchQuery.trim() || !map || isLoading) return;

        setIsLoading(true);
        setMessage(`'${searchQuery}' 위치 검색 중...`);
        clearRoute();

        try {
            const response = await fetch(`${LOCATION_API_URL}?query=${encodeURIComponent(searchQuery)}`, { method: 'GET', headers: { 'Content-Type': 'application/json' } });
            if (!response.ok) { throw new Error(`HTTP 오류! 상태 코드: ${response.status}`); }
            const data = await response.json();

            const lat = data.latitude ?? data.y;
            const lng = data.longitude ?? data.x;
            if (typeof lat === 'number' && typeof lng === 'number') {
                const newId = Date.now();
                const newMarker = { id: newId, lat, lng, name: data.query || searchQuery };

                setUserMarkers(prev => [...prev, newMarker]);
                setMessage(`'${newMarker.name}' 마커가 추가되었습니다.`);
                try {
                    if (map) {
                        map.setCenter(new window.naver.maps.LatLng(newMarker.lat, newMarker.lng));
                        map.setZoom(14, true);
                    }
                } catch (e) { console.warn('지도 중심 실패', e); }
            } else {
                setMessage(`'${searchQuery}'에 대한 유효한 좌표를 찾지 못했습니다.`);
            }
        } catch (error) {
            console.error('검색 중 오류 발생:', error);
            setMessage(`통신 오류: ${error.message}.`);

        } finally {
            setIsLoading(false);
        }
    };

    // --- 9. 자동완성 로직 ---
    useEffect(() => {
        const initAutocomplete = () => {
             try {
                if (!window.google || !window.google.maps || !window.google.maps.places) {
                    console.warn('Google Places가 준비되지 않았습니다.');
                    return;
                }
                const input = document.getElementById('autocomplete-input');
                if (!input) return;

                const autocomplete = new window.google.maps.places.Autocomplete(input, {
                    fields: ['name', 'geometry', 'formatted_address'],
                    types: ['geocode', 'establishment'],
                    componentRestrictions: { country: 'kr' }
                });

                autocomplete.addListener('place_changed', () => {
                    const place = autocomplete.getPlace();
                    if (!place || !place.geometry || !place.geometry.location) {
                        setMessage('❌ 선택된 장소의 위치 정보를 가져올 수 없습니다.');
                        return;
                    }

                    const lat = place.geometry.location.lat();
                    const lng = place.geometry.location.lng();
                    const newId = Date.now();
                    const name = place.name || place.formatted_address || '검색 결과';

                    const newMarker = { id: newId, lat, lng, name };

                    setUserMarkers(prev => [...prev, newMarker]);
                    setMessage(`'${name}' 자동완성으로 마커 추가됨.`);
                    try {
                        if (map) {
                            map.setCenter(new window.naver.maps.LatLng(lat, lng));
                            map.setZoom(14, true);
                        }
                    } catch (e) { console.warn('네이버 지도 중심 이동 실패', e); }
                });
            } catch (e) {
                console.warn('Autocomplete 초기화 중 예외', e);
            }
        };

        if (window.google && window.google.maps && window.google.maps.places) {
            initAutocomplete();
            return;
        }

        const scriptId = 'google-places-script';
        if (document.getElementById(scriptId)) {
            const t = setTimeout(initAutocomplete, 600);
            return () => clearTimeout(t);
        }

        if (!GOOGLE_API_KEY) {
            console.warn('REACT_APP_GOOGLE_API_KEY가 설정되지 않았습니다. 자동완성 기능 비활성화됩니다.');
            return;
        }

        const script = document.createElement('script');
        script.id = scriptId;
        script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_API_KEY}&libraries=places&language=ko`;
        script.async = true;
        script.defer = true;
        script.onload = () => { initAutocomplete(); };
        script.onerror = () => { console.warn('Google Places 스크립트 로드 실패'); };
        document.head.appendChild(script);

    }, [map]);

    // --- 10. 삭제 모드 ---
    useEffect(() => {
        if (!map || !mapObjectsRef || !mapObjectsRef.current) return;

        const markerKeys = Object.keys(mapObjectsRef.current).filter(k => {
            const n = Number(k);
            return !Number.isNaN(n);
        });

        if (isDeleteMode) {
            markerKeys.forEach(key => {
                if (deleteListenersRef.current[key]) return;
                const markerObj = mapObjectsRef.current[key];
                try {
                    const listener = window.naver.maps.Event.addListener(markerObj, 'click', () => {
                        try {
                            handleDeleteMarker(Number(key));
                            setMessage('🗑 마커가 삭제되었습니다.');
                        } catch (e) {
                            console.warn('삭제 핸들러 실행 중 오류', e);
                        }
                    });
                    deleteListenersRef.current[key] = listener;
                } catch (e) {
                    console.warn('삭제 리스너 등록 실패', e);
                }
            });
            setMessage('🗑 삭제 모드 활성화 — 삭제하려면 마커를 클릭하세요.');
        } else {
            Object.keys(deleteListenersRef.current).forEach(key => {
                try {
                    const listener = deleteListenersRef.current[key];
                    if (listener && window.naver && window.naver.maps && window.naver.maps.Event) {
                        window.naver.maps.Event.removeListener(listener);
                    }
                } catch (e) { /* 무시 */ }
            });
            deleteListenersRef.current = {};
            setMessage(prev => prev || '삭제 모드가 해제되었습니다.');
        }

        return () => {
            if (!deleteListenersRef.current) return;
            Object.keys(deleteListenersRef.current).forEach(key => {
                try {
                    const listener = deleteListenersRef.current[key];
                    if (listener && window.naver && window.naver.maps && window.naver.maps.Event) {
                        window.naver.maps.Event.removeListener(listener);
                    }
                } catch (e) { /* 무시 */ }
            });
            deleteListenersRef.current = {};
        };
    }, [isDeleteMode, map, mapObjectsRef, handleDeleteMarker]);

    // --- 11. 경로 생성 시작 핸들러 ---
    const handleGenerateRoute = async () => {
        clearRoute();

        if (userMarkers.length < 2) {
            setMessage('⚠️ 경로 생성을 시작하려면 지도에 최소 두 개 이상의 마커가 있어야 합니다.');
            return;
        }

        setSelectedStartId(null);
        setSelectedEndId(null);
        setIsSelectingPath(true);
        setMessage('✨ Start path creation mode! 1️⃣ Click the origin marker.');
    };

    // --- 12. UI 렌더링 (JSX) ---
    return (
        <div className="kpath-container-map-only">
            
            {/* 검색 UI */}
            <form onSubmit={handleSearch} className="kpath-search-form" style={{ alignItems: 'center' }}>
                <input
                    id="autocomplete-input"
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search for a place or address and add it to the map as a marker."
                    className="kpath-search-input"
                    disabled={isLoading}
                    autoComplete="off"
                />
                <button type="submit" className="kpath-search-button" disabled={isLoading || !isApiLoaded} >
                    {isLoading ? (<Loader className="w-5 h-5" style={{ animation: 'spin 1s linear infinite', marginRight: '0.5rem' }} />) : (<Search className="w-5 h-5" style={{ marginRight: '0.5rem' }} />)}
                    Search for places and add markers
                </button>

                {/* 삭제 모드 토글 버튼 */}
                <button
                    type="button"
                    onClick={() => setIsDeleteMode(prev => !prev)}
                    className="kpath-delete-toggle"
                    style={{
                        background: isDeleteMode ? '#ef4444' : '#6b7280',
                        color: 'white',
                        padding: '0.5rem 0.7rem',
                        borderRadius: 7,
                        border: 'none',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',   
                        justifyContent: 'center',           
                        gap: '0.5rem'
                    }}
                >
                    <Trash2 className="w-5 h-5" />
                    {isDeleteMode ? 'Delete Mode (ON)' : 'Delete Mode (OFF)'}
                </button>
            </form>

            {/* 경로 컨트롤 박스 */}
            <div className="kpath-route-control-box">
                <div className="kpath-control-item">
                    <span className="kpath-bold-text" style={{ color: selectedStartId ? '#16a34a' : '#30415eff' }}>Departure:</span>
                    <span style={{ marginLeft: '0.5rem',color: '#888888'}}>{selectedStartId ? userMarkers.find(m => m.id === selectedStartId)?.name : 'Unspecified'}</span>
                </div>
                <div className="kpath-control-item">
                    <span className="kpath-bold-text" style={{ color: selectedEndId ? '#dc2626' : '#30415eff' }}>Destination:</span>
                    <span style={{ marginLeft: '0.5rem',color: '#888888'}}>{selectedEndId ? userMarkers.find(m => m.id === selectedEndId)?.name : 'Unspecified'}</span>
                </div>
                <button
                    onClick={handleGenerateRoute}
                    className={`kpath-generate-button ${isSelectingPath ? 'kpath-generate-button-selecting' : ''}`}
                    disabled={isLoading || userMarkers.length < 2 || isSelectingPath}
                >
                    {isSelectingPath ? (<><Loader className="w-5 h-5" style={{ animation: 'spin 1s linear infinite', marginRight: '0.5rem' }} /> Selecting a marker...</>) : (<><Route className="w-5 h-5" style={{ marginRight: '0.5rem' }} /> Start Path Creation!</>)}
                </button>
            </div>
             {/* 지도 컨테이너 */}
            <div className="kpath-map-outer-container">
                <div id="map" className="w-full h-full" style={{ display: isApiLoaded ? 'block' : 'none', minHeight: '500px' }} />
            </div>  

            {/* 상태 메시지 및 경로 요약 */}
            <div className={`kpath-message-box ${isLoading ? 'loading' : 'success'}`}>
                <p className="kpath-message-text">
                    <MapPin className="w-5 h-5" style={{ marginRight: '0.5rem' }} /> <strong>{message}</strong>
                </p>
            </div>

            {isSummaryVisible && routeResult && (
                <div className="kpath-route-summary-box">
                    <h3 className="kpath-summary-title"><BusFront className="w-6 h-6" style={{ marginRight: '0.5rem' }} /> Recommended public transportation route</h3>
                    <div className="kpath-summary-info">
                        <p>⏱ Total Time: <b className="text-indigo-600">{routeResult.totalTime ?? '-'}min</b></p>
                        <p>💰 Fare: <b className="text-indigo-600">{routeResult.fare ?? '-'}KRW</b></p>

                    </div>
                    <div className="kpath-detail-list">
                        {routeResult.subPath && Array.isArray(routeResult.subPath) && routeResult.subPath.map((path, index) => (
                            <SubPathItem key={index} path={path} index={index} subPathArray={routeResult.subPath} />
                        ))}
                    </div>
                </div>
            )}

            {/* 마커 메모 모달 렌더링 */}
            {modalContent && <MemoModal {...modalContent} />}

        </div>
    );
}

export default KPathIdeaPage;
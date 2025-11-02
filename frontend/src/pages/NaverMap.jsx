// src/components/NaverMap.jsx (URL 수정된 버전)
import React, { useEffect, useRef, useState } from 'react';

const NAVER_MAPS_CLIENT_ID = process.env.REACT_APP_NAVER_MAPS_CLIENT_ID;
const NAVER_MAPS_URL = `https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId=${NAVER_MAPS_CLIENT_ID}&language=en&submodules=geocoder`;

const NaverMap = () => {
    const mapElement = useRef(null);
    const mapLoaded = useRef(false);
    const [map, setMap] = useState(null);
    const [markers, setMarkers] = useState([]);

    useEffect(() => {
        const initializeMap = () => {
            if (mapLoaded.current || !window.naver || !window.naver.maps) return;

            if (mapElement.current) {
                mapLoaded.current = true;

                const mapOptions = {
                    center: new window.naver.maps.LatLng(37.5665, 126.9780),
                    zoom: 12,
                    mapTypeId: window.naver.maps.MapTypeId.NORMAL
                };

                const newMap = new window.naver.maps.Map(mapElement.current, mapOptions);
                setMap(newMap);
            }
        };

        if (window.naver && window.naver.maps) {
            initializeMap();
            return;
        }

        const script = document.createElement('script');
        script.src = NAVER_MAPS_URL;
        script.async = true;
        script.onload = initializeMap;
        script.onerror = () => console.error("네이버 지도 API 로드 실패. Client ID 확인 필요");
        document.head.appendChild(script);

        return () => {
            if (document.head.contains(script)) {
                document.head.removeChild(script);
            }
        };
    }, []);

    // 전역 함수로 마커 추가 기능 제공
    useEffect(() => {
        if (map) {
            window.addFestivalMarkers = (mapMarkers) => {
                addMarkers(mapMarkers);
            };
        }
    }, [map]);

    // 🎯 destinations 테이블에 추가하는 함수 (일차 포함)
    const addToDestinations = async (markerData, festivalId) => {
        try {
            const sessionId = localStorage.getItem('session_id');
            if (!sessionId) {
                alert('로그인이 필요합니다.');
                return;
            }

            // 입력된 일차 값 가져오기
            const dayInput = document.getElementById(`dayInput_${festivalId}`);
            const dayNumber = parseInt(dayInput.value) || 1;
            
            // 유효성 검사
            if (dayNumber < 1 || dayNumber > 30) {
                alert('❌ 1일차부터 30일차까지만 입력 가능합니다.');
                return;
            }

            const destinationData = {
                name: markerData.title,
                day_number: dayNumber,  // 사용자가 입력한 일차
                place_type: 2, // 축제는 2
                reference_id: markerData.id || markerData.festival_id || null,  // 🎯 둘 다 시도
                latitude: parseFloat(markerData.latitude),
                longitude: parseFloat(markerData.longitude)
            };

            const response = await fetch('http://localhost:8000/api/destinations/add', {  // ✅ URL 수정
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${sessionId}`
                },
                body: JSON.stringify(destinationData)
            });

            if (response.ok) {
                alert(`✅ "${markerData.title}"이(가) ${dayNumber}일차 일정에 추가되었습니다!`);
            } else {
                const error = await response.json();
                alert(`❌ 추가 실패: ${error.message || '오류가 발생했습니다.'}`);
            }
        } catch (error) {
            console.error('Error adding destination:', error);
            alert('❌ 목적지 추가 중 오류가 발생했습니다.');
        }
    };

    const addMarkers = (mapMarkers) => {
        if (!map || !mapMarkers || mapMarkers.length === 0) return;

        // 기존 마커들 제거
        markers.forEach(marker => marker.setMap(null));
        
        const newMarkers = [];

        mapMarkers.forEach((markerData) => {
            if (markerData.latitude && markerData.longitude) {
                // 기본 마커 생성
                const marker = new window.naver.maps.Marker({
                    position: new window.naver.maps.LatLng(markerData.latitude, markerData.longitude),
                    map: map,
                    title: markerData.title
                });

                // 🎯 일차 입력이 포함된 Add 버튼 정보창
                const infoWindow = new window.naver.maps.InfoWindow({
                    content: `
                        <div style="padding: 15px; max-width: 250px; font-family: Arial, sans-serif;">
                            <h4 style="margin: 0 0 8px 0; color: #333; font-size: 16px; font-weight: bold;">
                                ${markerData.title}
                            </h4>
                            ${markerData.start_date && markerData.end_date ? `
                                <p style="margin: 5px 0; font-size: 13px; color: #666; background: #f0f0f0; padding: 4px 8px; border-radius: 4px;">
                                    📅 ${markerData.start_date} ~ ${markerData.end_date}
                                </p>
                            ` : ''}
                            
                            <!-- 일차 입력 필드 추가 -->
                            <div style="margin: 10px 0; text-align: center;">
                                <input 
                                    type="number" 
                                    id="dayInput_${markerData.festival_id}" 
                                    placeholder="몇일차?" 
                                    min="1" 
                                    max="30"
                                    value="1"
                                    style="
                                        width: 80px;
                                        padding: 6px 8px;
                                        border: 2px solid #ddd;
                                        border-radius: 4px;
                                        text-align: center;
                                        font-size: 14px;
                                        margin-right: 8px;
                                    "
                                />
                                <span style="font-size: 13px; color: #666;">일차</span>
                            </div>
                            
                            <div style="margin-top: 12px; text-align: center;">
                                <button 
                                    onclick="addToDestinations_${markerData.festival_id || 'unknown'}()" 
                                    style="
                                        background: #ff4444;
                                        color: white;
                                        border: none;
                                        padding: 8px 16px;
                                        border-radius: 6px;
                                        cursor: pointer;
                                        font-size: 13px;
                                        font-weight: bold;
                                        box-shadow: 0 2px 4px rgba(255, 68, 68, 0.3);
                                        transition: all 0.3s ease;
                                    "
                                    onmouseover="this.style.background='#ff3333'; this.style.transform='translateY(-1px)'"
                                    onmouseout="this.style.background='#ff4444'; this.style.transform='translateY(0px)'"
                                >
                                    ➕ Add
                                </button>
                            </div>
                        </div>
                    `
                });

                // 🎯 각 마커별 고유한 전역 함수 생성 (일차 포함)
                window[`addToDestinations_${markerData.festival_id || 'unknown'}`] = () => {
                    addToDestinations(markerData, markerData.festival_id);
                };

                // 마커 클릭 시 정보창 표시
                window.naver.maps.Event.addListener(marker, 'click', () => {
                    infoWindow.open(map, marker);
                });

                newMarkers.push(marker);
            }
        });

        setMarkers(newMarkers);

        // 첫 번째 마커 위치로 지도 이동
        if (newMarkers.length > 0) {
            const firstMarker = mapMarkers[0];
            map.setCenter(new window.naver.maps.LatLng(firstMarker.latitude, firstMarker.longitude));
            map.setZoom(13);
        }
    };

    return (
        <div
            ref={mapElement}
            style={{
                width: '100%',
                height: '100%',
                minHeight: '400px',
            }}
        >
            {!mapLoaded.current && (
                <div style={{ padding: '20px', textAlign: 'center' }}>
                    지도를 로딩 중입니다...
                </div>
            )}
        </div>
    );
};

export default NaverMap;
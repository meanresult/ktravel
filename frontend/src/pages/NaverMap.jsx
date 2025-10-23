// src/components/NaverMap.jsx
import React, { useEffect, useRef } from 'react';

// .env 파일에서 키 값 가져오기 (Vite 환경)

//const NAVER_MAPS_CLIENT_ID ="lqri8w9xmo"
const NAVER_MAPS_CLIENT_ID = process.env.REACT_APP_NAVER_MAPS_CLIENT_ID;
const NAVER_MAPS_URL = `https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId=${NAVER_MAPS_CLIENT_ID}&language=en&submodules=geocoder`;

const NaverMap = () => {
    const mapElement = useRef(null);
    const mapLoaded = useRef(false);

    useEffect(() => {
        const initializeMap = () => {
            if (mapLoaded.current || !window.naver || !window.naver.maps) return;

            if (mapElement.current) {
                mapLoaded.current = true;

                const mapOptions = {
                    center: new window.naver.maps.LatLng(37.5665, 126.9780), // 서울 시청 중심
                    zoom: 12,
                    mapTypeId: window.naver.maps.MapTypeId.NORMAL
                };

                new window.naver.maps.Map(mapElement.current, mapOptions);
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
            document.head.removeChild(script);
        };
    }, []);

    return (
        <div
            ref={mapElement}
            style={{
                width: '100%',      // 부모 너비 100%
                height: '100%',     // 부모 높이 100%
                minHeight: '400px', // 최소 높이 지정 (선택 사항)
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

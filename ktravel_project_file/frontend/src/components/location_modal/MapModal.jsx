// src/components/location_modal/MapModal.jsx
import React, { useEffect, useRef, useState } from 'react';
import './MapModal.css';
import ConcertMarkerImg from '../../assets/concert_marker.png';

// ✅ 네이버 지도 키
const NAVER_MAPS_CLIENT_ID = process.env.REACT_APP_NAVER_MAPS_CLIENT_ID;
const NAVER_MAPS_URL = `https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId=${NAVER_MAPS_CLIENT_ID}`;

const MapModal = ({ concert, onClose, onAddSchedule }) => {
    const mapElement = useRef(null);
    const [mapReady, setMapReady] = useState(false);

    const concertLocation =
        (concert.latitude && concert.longitude)
            ? { lat: concert.latitude, lng: concert.longitude }
            : null;

    // ✅ API script 로드 (중복되지 않게)
    useEffect(() => {
        if (!NAVER_MAPS_CLIENT_ID) return;

        const checkReady = () => {
            if (window.naver?.maps) {
                setMapReady(true);
            } else {
                setTimeout(checkReady, 100);
            }
        };

        if (!document.getElementById("naver-map-script")) {
            const script = document.createElement("script");
            script.src = NAVER_MAPS_URL;
            script.async = true;
            script.id = "naver-map-script";
            script.onload = checkReady;
            document.head.appendChild(script);
        } else {
            checkReady();
        }
    }, []);

    // ✅ 지도 & 커스텀 마커 렌더링
    useEffect(() => {
        if (!mapReady || !mapElement.current || !concertLocation) return;

        const naver = window.naver;
        const mapCenter = new naver.maps.LatLng(concertLocation.lat, concertLocation.lng);

        const map = new naver.maps.Map(mapElement.current, {
            center: mapCenter,
            zoom: 15,
            scaleControl: true,
        });

        // ✅ 커스텀 마커
        new naver.maps.Marker({
            position: mapCenter,
            map: map,
            icon: {
                url: ConcertMarkerImg,
                size: new naver.maps.Size(50, 50),
                scaledSize: new naver.maps.Size(38, 45),
                anchor: new naver.maps.Point(20, 40),
            },
            title: concert.title,
        });

    }, [mapReady, concertLocation]);

    
    const handleAddClick = () => {
        onAddSchedule(concert);
        onClose();
    };

    return (
        <div className="map-modal-overlay" onClick={onClose}>
            <div className="map-modal-content" onClick={(e) => e.stopPropagation()}>
                <button className="map-modal-close" onClick={onClose}>×</button>

                <h2>{concert.title} Location</h2>
                <p className="modal-place-name">Place: {concert.place}</p>

                <div
                    ref={mapElement}
                    className="map-container"
                    style={{ height: "350px" }}
                >
                    {!mapReady && (
                        <p style={{ textAlign: "center", paddingTop: "150px" }}>
                            Loading Map API...
                        </p>
                    )}
                    {mapReady && !concertLocation && (
                        <p style={{ textAlign: "center", paddingTop: "150px", color: "red" }}>
                            Error: Location coordinates not available.
                        </p>
                    )}
                </div>

                <button
                    className="modal-add-schedule-button"
                    onClick={handleAddClick}
                >
                    Add Place to Schedule 💜
                </button>
            </div>
        </div>
    );
};

export default MapModal;

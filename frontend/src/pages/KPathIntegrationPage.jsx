import React, { useState, useEffect } from 'react';
import KPathIdeaPage from './KPathIdeaPage.jsx'; 
import ScheduleTable from './ScheduleTable.jsx'; 
import '../styles/KPathIntegrationPage.css';

/**
 * 지도와 일정 테이블을 통합하고 중앙 상태를 관리하는 메인 페이지 컴포넌트
 */
function KPathIntegrationPage() {
  // ⭐ 선택된 day_title 상태 추가
  const [selectedDayTitle, setSelectedDayTitle] = useState('');
  
  // ⭐ 해당 일정의 목적지들 (지도에 표시될 마커들)
  const [scheduleLocations, setScheduleLocations] = useState([]);
  
  // ⭐ 로딩 상태
  const [isLoadingDestinations, setIsLoadingDestinations] = useState(false);
  
  // 기존 상태 (지도 중심 이동용 - 옵션)
  const [selectedSchedule, setSelectedSchedule] = useState(null);

  // 페이지 마운트 시 body에 클래스 추가
  useEffect(() => {
    document.body.classList.add('kpath-page-body');
    return () => {
      document.body.classList.remove('kpath-page-body');
    };
  }, []);

  // ⭐ day_title 변경 시 해당 일정의 목적지들 가져오기
  useEffect(() => {
    if (!selectedDayTitle) {
      setScheduleLocations([]);
      return;
    }

    const fetchDestinations = async () => {
      setIsLoadingDestinations(true);
      const token = localStorage.getItem('session_id');
      
      if (!token) {
        console.warn('⚠️ 토큰이 없습니다.');
        setIsLoadingDestinations(false);
        return;
      }

      try {
        console.log(`🔍 "${selectedDayTitle}" 일정의 목적지 조회 시작`);
        
        const response = await fetch(
          `http://localhost:8000/api/destinations/by-schedule?day_title=${encodeURIComponent(selectedDayTitle)}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: 목적지 조회 실패`);
        }

        const destinations = await response.json();
        console.log(`✅ Destinations fetched (${destinations.length}):`, destinations);

        // KPathIdeaPage의 마커 형식으로 변환
        const markers = destinations.map(dest => ({
          id: dest.destination_id,
          lat: dest.latitude,
          lng: dest.longitude,
          name: dest.name,
          notes: dest.notes || ''
        }));

        setScheduleLocations(markers);
        
      } catch (error) {
        console.error('❌ 목적지 조회 실패:', error);
        setScheduleLocations([]);
      } finally {
        setIsLoadingDestinations(false);
      }
    };

    fetchDestinations();
  }, [selectedDayTitle]);

  // ⭐ ScheduleTable에서 day_title 변경 시 호출되는 핸들러
  const handleDayTitleChange = (dayTitle) => {
    console.log(`📅 일정 선택됨: ${dayTitle}`);
    setSelectedDayTitle(dayTitle);
  };

  // 기존 일정 선택 핸들러 (필요시 유지)
  const handleScheduleSelect = (schedule) => {
    setSelectedSchedule({
      id: schedule.id,
      name: schedule.name,
      lat: schedule.lat,
      lng: schedule.lng,
    });
  };

  return (
    <div className="kpath-container-main">
      
      {/* 1. 왼쪽 일정 관리 패널 */}
      <div className="kpath-schedule-panel">
        <header className="kpath-header-wrapper">
          <h1 className="kpath-header-title">
            K-Path Travel Idea&nbsp;
            <svg width="5%" height="20%" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M5 14.2864C3.14864 15.1031 2 16.2412 2 17.5C2 19.9853 6.47715 22 12 22C17.5228 22 22 19.9853 22 17.5C22 16.2412 20.8514 15.1031 19 14.2864M18 8C18 12.0637 13.5 14 12 17C10.5 14 6 12.0637 6 8C6 4.68629 8.68629 2 12 2C15.3137 2 18 4.68629 18 8ZM13 8C13 8.55228 12.5523 9 12 9C11.4477 9 11 8.55228 11 8C11 7.44772 11.4477 7 12 7C12.5523 7 13 7.44772 13 8Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </h1>
          <p className="kpath-header-subtitle">Create Your Own Korea Travel Itinerary</p>
        </header>

        {/* ⭐ ScheduleTable에 onDayTitleChange 콜백 전달 */}
        <ScheduleTable 
          onDayTitleChange={handleDayTitleChange}
          onSelectSchedule={handleScheduleSelect} 
          selectedId={selectedSchedule ? selectedSchedule.id : null}
        />
        
        {/* ⭐ 로딩 상태 표시 (옵션) */}
        {isLoadingDestinations && (
          <div style={{ 
            padding: '1rem', 
            textAlign: 'center', 
            color: '#6366f1',
            fontWeight: 'bold' 
          }}>
            📍 Loading destination...
          </div>
        )}
        
        {/* ⭐ 목적지 개수 표시 (옵션) */}
        {!isLoadingDestinations && scheduleLocations.length > 0 && (
          <div style={{ 
            padding: '0.5rem 1rem', 
            textAlign: 'center', 
            color: '#10b981',
            fontSize: '0.9rem' 
          }}>
            ✅ {scheduleLocations.length} destinations were shown on the map 
          </div>
        )}
      </div>

      {/* 2. 오른쪽 지도/검색 패널 */}
      <div className="kpath-map-panel">
        {/* ⭐ scheduleLocations를 KPathIdeaPage에 전달 */}
        <KPathIdeaPage 
          scheduleLocation={selectedSchedule}
          scheduleLocations={scheduleLocations}
        />
      </div>
    </div>
  );
}

export default KPathIntegrationPage;
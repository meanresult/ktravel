// src/pages/ConcertPage.jsx
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import api from '../services/api';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';
import '../styles/ConcertPage.css';
import MapModal from '../components/location_modal/MapModal';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const MAX_BUTTONS = 6;

const formatDate = (date) => {
    if (!date) return '';
    const d = new Date(date);
    let month = '' + (d.getMonth() + 1);
    let day = '' + d.getDate();
    const year = d.getFullYear();

    if (month.length < 2) month = '0' + month;
    if (day.length < 2) day = '0' + day;

    return [year, month, day].join('-');
};

// ✅ ScheduleTable과 동일한 인증 함수
const globalFetchWithAuth = async (url, options = {}, token, setToken, setAuthError) => {
    setAuthError(null);
    if (!token) {
        const error = new Error("세션이 없습니다. 로그인해주세요");
        setAuthError(error.message);
        throw error;
    }
    const headers = {
        ...options.headers,
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
    try {
        const response = await fetch(url, { ...options, headers });
        if (response.status === 401) {
            const error = new Error('로그인이 만료되었습니다. 다시 로그인해주세요.');
            setAuthError(error.message);
            localStorage.removeItem('session_id');
            setToken(null);
            setTimeout(() => { window.location.href = '/'; }, 2000);
            throw error;
        }
        if (!response.ok) {
            const errorDetail = await response.json().catch(() => ({}));
            console.error('🔍 API 에러 상세:', errorDetail);
            console.error('🔍 HTTP 상태:', response.status);
            const errorMessage = errorDetail.detail || `API 요청 실패: ${response.status} ${response.statusText}`;
            throw new Error(errorMessage);
        }
        return response;
    } catch (error) {
        console.error("❌ fetch 실패:", error);
        throw error;
    }
};

const ConcertCard = ({ concert, handleViewMap, handleAddSchedule }) => {
    const dateRange =
        concert.start_date === concert.end_date
            ? formatDate(concert.start_date)
            : `${formatDate(concert.start_date)} - ${formatDate(concert.end_date)}`;

    const handleMapAndAddClick = (concert) => {
        handleViewMap(concert); 
    };

    return (
        <div className="concert-card-container">
            <div className="concert-card-image-box">
                <img
                    src={concert.image || '/default-kpop-image.png'}
                    alt={concert.title}
                    className="concert-card-image"
                />
            </div>
            <div className="concert-card-details">
                <h3 className="concert-card-title">{concert.title}</h3>
                <p className="concert-card-date">{dateRange}</p>
                {concert.place && <p className="concert-card-place">{concert.place}</p>}
                <p className="concert-card-genre">Concert</p>

                <div className="concert-card-actions">
                    {concert.place && (
                        <button
                            className="concert-view-map-button"
                            onClick={() => handleMapAndAddClick(concert)}
                        >
                            Map & Add
                        </button>
                    )}
                    
                    <a
                        href={concert.link || '#'}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="concert-get-tickets-button"
                    >
                        Get Tickets →
                    </a>
                </div>
            </div>
        </div>
    );
};

const CalendarEventItem = ({ concert }) => {
    const iconColor = concert.place?.includes('대학교') ? '#5cb85c' : '#f0ad4e';
    const dateRange =
        concert.start_date === concert.end_date
            ? formatDate(concert.start_date)
            : `${formatDate(concert.start_date)} ~ ${formatDate(concert.end_date)}`;

    return (
        <div className="concert-calendar-event-item">
            <span className="concert-event-icon" style={{ backgroundColor: iconColor }}></span>
            <span className="concert-event-title">{concert.title}</span>
            <span className="concert-event-date">{dateRange}</span>
        </div>
    );
};

const ConcertPage = ({ isEmbedded }) => {
    const [concerts, setConcerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [calendarDate, setCalendarDate] = useState(new Date());
    const [searchTerm, setSearchTerm] = useState('');
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 6;
    
    // 🆕 인증 관련 state
    const [token, setToken] = useState(localStorage.getItem('session_id'));
    const [authError, setAuthError] = useState(null);
    
    // 지도 모달 관련
    const [selectedConcert, setSelectedConcert] = useState(null);
    
    // 🆕 일정 선택 팝업 관련 state
    const [showSchedulePopup, setShowSchedulePopup] = useState(false);
    const [schedules, setSchedules] = useState([]);
    const [selectedSchedule, setSelectedSchedule] = useState(null);
    const [isLoadingSchedules, setIsLoadingSchedules] = useState(false);
    const [scheduleError, setScheduleError] = useState(null);
    const [concertToAdd, setConcertToAdd] = useState(null); // 추가할 콘서트 정보 저장

    const containerStyle = isEmbedded
        ? {
            padding: '20px',
            minHeight: '100%',
            maxWidth: 'none',
            margin: 0,
            backgroundColor: 'transparent',
        }
        : {};

    // ✅ fetchWithAuth 생성
    const fetchWithAuth = useCallback((url, options = {}) =>
        globalFetchWithAuth(url, options, token, setToken, setAuthError),
    [token]);

    useEffect(() => {
        document.body.classList.add('concert-page-body');
        return () => {
            document.body.classList.remove('concert-page-body');
        };
    }, []);

    useEffect(() => {
        const fetchConcerts = async () => {
            try {
                const response = await api.get('/api/concerts');
                setConcerts(response.data);
                setLoading(false);
            } catch (err) {
                console.error('데이터 로딩 실패:', err);
                setError('콘서트 데이터를 불러오는 데 실패했습니다.');
                setLoading(false);
            }
        };
        fetchConcerts();
    }, []);

    useEffect(() => {
        setCurrentPage(1);
    }, [searchTerm]);
    
    // 지도 보기 핸들러
    const handleViewMap = (concert) => {
        setSelectedConcert(concert);
    };

    // 🆕 일정 목록 가져오기
    const fetchSchedules = async () => {
        setIsLoadingSchedules(true);
        setScheduleError(null);
        
        console.log('🔍 fetchSchedules - token 확인:', token ? '존재함' : '없음');
        
        if (!token) {
            setScheduleError('로그인이 필요합니다.');
            setIsLoadingSchedules(false);
            return;
        }
        
        try {
            const response = await fetchWithAuth(`${API_URL}/api/schedules/day_titles`);
            const data = await response.json();
            
            console.log('✅ 일정 목록 조회 성공:', data);
            setSchedules(data);
            
        } catch (error) {
            console.error('❌ 일정 목록 조회 실패:', error);
            setScheduleError(error.message);
        } finally {
            setIsLoadingSchedules(false);
        }
    };

    // 🆕 장소 추가 핸들러 (모달 또는 카드에서 호출)
    const handleAddSchedule = (concert) => {
        console.log("🔍 ConcertPage가 받은 concert:", concert);
        console.log('🔍 handleAddSchedule 호출됨');
        
        setConcertToAdd(concert); // 추가할 콘서트 저장
        setShowSchedulePopup(true);
        fetchSchedules();
    };
    
    // 🆕 일정 선택 핸들러
    const handleScheduleSelect = (schedule) => {
        setSelectedSchedule(schedule);
    };
    
    // 🆕 일정에 목적지 추가 확정 - API 호출!
    const handleConfirmAddToSchedule = async () => {
        if (!selectedSchedule || !concertToAdd) {
            alert('일정을 선택해주세요.');
            return;
        }
        
        console.log('🔍 콘서트 장소 추가 시작:', {
            schedule: selectedSchedule,
            concert: concertToAdd
        });
        
        // day_title에서 숫자 추출 (예: "1days" -> 1)
        const dayNumber = parseInt(selectedSchedule.day_title.match(/\d+/)?.[0] || '1');
        
        try {
            setIsLoadingSchedules(true);
            
            // 요청 데이터 구성
            const requestData = {
                day_number: dayNumber,
                name: concertToAdd.place,
                place_type: 1,
                reference_id: concertToAdd.id,
                latitude: parseFloat(concertToAdd.latitude) || null,
                longitude: parseFloat(concertToAdd.longitude) || null,
                visit_order: null,
                notes: concertToAdd.title
            };
            
            console.log('🔍 API 요청 데이터:', requestData);
            console.log('🔍 각 필드 타입 확인:', {
                day_number: typeof requestData.day_number,
                name: typeof requestData.name,
                place_type: typeof requestData.place_type,
                reference_id: typeof requestData.reference_id,
                latitude: typeof requestData.latitude,
                longitude: typeof requestData.longitude,
                visit_order: requestData.visit_order,
                notes_length: requestData.notes?.length || 0
            });
            
            // 🎯 실제 API 호출!
            const response = await fetchWithAuth(`${API_URL}/api/destinations/add`, {
                method: 'POST',
                body: JSON.stringify(requestData)
            });
            
            const result = await response.json();
            
            console.log('✅ 콘서트 장소 추가 API 성공:', result);
            
            // 팝업 닫기
            setShowSchedulePopup(false);
            setSelectedSchedule(null);
            setConcertToAdd(null);
            
            // 성공 메시지
            alert(result.message || `"${concertToAdd.title}"이(가) "${selectedSchedule.day_title}"에 추가되었습니다! 🎉`);
            
        } catch (error) {
            console.error('❌ 콘서트 장소 추가 실패:', error);
            alert(`장소 추가 실패: ${error.message}`);
        } finally {
            setIsLoadingSchedules(false);
        }
    };
    
    // 🆕 일정 선택 팝업 닫기
    const handleCloseSchedulePopup = () => {
        setShowSchedulePopup(false);
        setSelectedSchedule(null);
        setScheduleError(null);
        setConcertToAdd(null);
    };

    const filteredByCalendar = useMemo(() => {
        if (!calendarDate) return [];

        const selectedDate = new Date(calendarDate);
        selectedDate.setHours(0, 0, 0, 0);

        return concerts.filter((concert) => {
            const start = new Date(concert.start_date);
            const end = new Date(concert.end_date);

            start.setHours(0, 0, 0, 0);
            end.setHours(0, 0, 0, 0);

            return selectedDate >= start && selectedDate <= end;
        });
    }, [concerts, calendarDate]);

    const { currentItems, totalPages, displayPageNumbers } = useMemo(() => {
        const filtered = concerts.filter((concert) =>
            concert.title.toLowerCase().includes(searchTerm.toLowerCase())
        );

        const totalPages = Math.ceil(filtered.length / itemsPerPage);

        const indexOfLastItem = currentPage * itemsPerPage;
        const indexOfFirstItem = indexOfLastItem - itemsPerPage;

        const currentItems = filtered.slice(indexOfFirstItem, indexOfLastItem);

        if (currentPage > totalPages && totalPages > 0) {
            setCurrentPage(totalPages);
        }

        let startPage = Math.max(1, currentPage - Math.floor(MAX_BUTTONS / 2));
        if (startPage + MAX_BUTTONS - 1 > totalPages) {
            startPage = Math.max(1, totalPages - MAX_BUTTONS + 1);
        }

        const endPage = Math.min(totalPages, startPage + MAX_BUTTONS - 1);
        const displayPageNumbers = [];
        for (let i = startPage; i <= endPage; i++) displayPageNumbers.push(i);

        return { currentItems, totalPages, displayPageNumbers };
    }, [concerts, currentPage, itemsPerPage, searchTerm]);

    const handlePageChange = (pageNumber) => {
        setCurrentPage(pageNumber);
    };

    const handleSearchChange = (event) => {
        setSearchTerm(event.target.value);
    };

    const tileContent = ({ date, view }) => {
        if (view === 'month') {
            const dateStr = formatDate(date);

            const hasEvent = concerts.some((concert) => {
                const start = new Date(concert.start_date);
                const end = new Date(concert.end_date);
                const current = new Date(dateStr);

                start.setHours(0, 0, 0, 0);
                end.setHours(0, 0, 0, 0);
                current.setHours(0, 0, 0, 0);

                return current >= start && current <= end;
            });

            if (hasEvent) {
                return <div className="concert-event-dot"></div>;
            }
        }
        return null;
    };

    if (loading) return <div style={containerStyle}>Loading...</div>;
    if (error) return <div style={containerStyle}>error: {error}</div>;

    return (
        <div className="concert-page" style={containerStyle}>
            
            {/* MapModal에도 handleAddSchedule 전달 */}
            {selectedConcert && (
                <MapModal 
                    concert={selectedConcert} 
                    onClose={() => setSelectedConcert(null)}
                    onAddSchedule={handleAddSchedule}
                />
            )}

            {/* 🆕 일정 선택 팝업 */}
            {showSchedulePopup && (
                <div className="schedule-select-overlay" onClick={handleCloseSchedulePopup}>
                    <div className="schedule-select-popup" onClick={(e) => e.stopPropagation()}>
                        
                        <button className="schedule-close-btn" onClick={handleCloseSchedulePopup}>✕</button>
                        
                        <h2 className="schedule-popup-title">📅 일정 선택</h2>
                        <p className="schedule-popup-subtitle">
                            "{concertToAdd?.title}"을(를) 추가할 일정을 선택하세요
                        </p>
                        
                        {authError && (
                            <div className="schedule-error">
                                <p>❌ {authError}</p>
                            </div>
                        )}
                        
                        {isLoadingSchedules && (
                            <div className="schedule-loading">
                                <p>⏳ 일정 목록을 불러오는 중...</p>
                            </div>
                        )}
                        
                        {scheduleError && !authError && (
                            <div className="schedule-error">
                                <p>❌ {scheduleError}</p>
                            </div>
                        )}
                        
                        {!isLoadingSchedules && !scheduleError && !authError && schedules.length === 0 && (
                            <div className="schedule-empty">
                                <p>등록된 일정이 없습니다.</p>
                                <p>먼저 일정을 생성해주세요.</p>
                            </div>
                        )}
                        
                        {!isLoadingSchedules && !scheduleError && !authError && schedules.length > 0 && (
                            <div className="schedule-list">
                                {schedules.map((schedule) => (
                                    <div
                                        key={schedule.day_title}
                                        className={`schedule-item ${selectedSchedule?.day_title === schedule.day_title ? 'selected' : ''}`}
                                        onClick={() => handleScheduleSelect(schedule)}
                                    >
                                        <div className="schedule-item-icon">
                                            {selectedSchedule?.day_title === schedule.day_title ? '✅' : '📅'}
                                        </div>
                                        <div className="schedule-item-content">
                                            <h3 className="schedule-item-title">{schedule.day_title}</h3>
                                            {schedule.description && (
                                                <p className="schedule-item-description">{schedule.description}</p>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                        
                        <div className="schedule-popup-actions">
                            <button 
                                className="schedule-cancel-btn"
                                onClick={handleCloseSchedulePopup}
                            >
                                취소
                            </button>
                            <button 
                                className="schedule-confirm-btn"
                                onClick={handleConfirmAddToSchedule}
                                disabled={!selectedSchedule || isLoadingSchedules}
                            >
                                {isLoadingSchedules ? '추가 중...' : '선택 완료'}
                            </button>
                        </div>
                        
                    </div>
                </div>
            )}

            <header className="concert-page-header">
                <h1>K-POP Concert List & Ticketing Home!</h1>
            </header>

            <div className="concert-content-wrapper">
                <div className="concert-calendar-side-wrapper">
                    <section className="concert-calendar-section">
                        <div className="concert-calendar-box">
                            <Calendar
                                onChange={setCalendarDate}
                                value={calendarDate}
                                tileContent={tileContent}
                                locale="ko-KR"
                                formatDay={(locale, date) =>
                                    date.toLocaleString('en', { day: 'numeric' })
                                }
                            />
                        </div>
                    </section>

                    <section className="concert-calendar-events-section">
                        <h2 className="concert-calendar-events-title">
                            {formatDate(calendarDate)} ({filteredByCalendar.length} case)
                        </h2>

                        <div className="concert-calendar-events-list">
                            {filteredByCalendar.length > 0 ? (
                                filteredByCalendar.map((concert) => (
                                    <CalendarEventItem key={concert.id} concert={concert} />
                                ))
                            ) : (
                                <p className="concert-no-events-message">
                                    There are no concerts scheduled for the selected date.
                                </p>
                            )}
                        </div>
                    </section>
                </div>

                <section className="concert-list-section">
                    <div className="concert-header-wrapper">
                        <h2>Concert Information 
                            <svg width="4%" height="5%" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M9 18V6.35537C9 5.87383 9 5.63306 9.0876 5.43778C9.16482 5.26565 9.28917 5.11887 9.44627 5.0144C9.62449 4.89588 9.86198 4.8563 10.337 4.77714L19.137 3.31047C19.7779 3.20364 20.0984 3.15023 20.3482 3.243C20.5674 3.32441 20.7511 3.48005 20.8674 3.68286C21 3.91398 21 4.23889 21 4.8887V16M9 18C9 19.6568 7.65685 21 6 21C4.34315 21 3 19.6568 3 18C3 16.3431 4.34315 15 6 15C7.65685 15 9 16.3431 9 18ZM21 16C21 17.6568 19.6569 19 18 19C16.3431 19 15 17.6568 15 16C15 14.3431 16.3431 13 18 13C19.6569 13 21 14.3431 21 16Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                            </svg> 
                        </h2>

                        <div className="concert-search-bar">
                            <input
                                type="text"
                                placeholder="Search by title 🔍"
                                value={searchTerm}
                                onChange={handleSearchChange}
                            />
                        </div>
                    </div>
                

                    {currentItems.length > 0 ? (
                        <>
                            <div className="concert-cards-grid">
                                {currentItems.map((concert) => (
                                    <ConcertCard 
                                        key={concert.id} 
                                        concert={concert} 
                                        handleViewMap={handleViewMap}
                                        handleAddSchedule={handleAddSchedule}
                                    />
                                ))}
                            </div>

                            {totalPages > 1 && (
                                <div className="concert-pagination-controls">
                                    {displayPageNumbers.map((number) => (
                                        <button
                                            key={number}
                                            onClick={() => handlePageChange(number)}
                                            className={currentPage === number ? 'active' : ''}
                                            aria-label={`${number}페이지로 이동`}
                                        >
                                            {number}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </>
                    ) : (
                        <p className="concert-no-data-message">
                            {searchTerm
                                ? '검색 결과가 없습니다.'
                                : '현재 등록된 콘서트 정보가 없습니다.'}
                        </p>
                    )}
                </section>
            </div>
        </div>
    );
};

export default ConcertPage;
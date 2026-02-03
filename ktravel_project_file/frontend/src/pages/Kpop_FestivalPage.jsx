import React, { useState, useEffect, useMemo } from 'react';
import api from '../services/api';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css'; 
import '../styles/Kpop_FestivalPage.css'; 

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

const FestivalCard = ({ festival }) => {
    const dateRange = festival.start_date === festival.end_date
        ? formatDate(festival.start_date)
        : `${formatDate(festival.start_date)} - ${formatDate(festival.end_date)}`;

    return (
        <div className="festival-card-container">
            <div className="festival-card-image-box">
                <img 
                    src={festival.image || '/default-kpop-image.png'} 
                    alt={festival.title} 
                    className="festival-card-image" 
                />
            </div>
            <div className="festival-card-details">
                <h3 className="festival-card-title">{festival.title}</h3>
                <p className="festival-card-date">{dateRange}</p>
                <p className="festival-card-place">{festival.place}</p>
                <p className="festival-card-genre">Concert</p> 
                <p className="festival-card-restriction">Preschoolers are not allowed to enter</p>
                <a 
                    href={festival.link || '#'} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="get-tickets-button"
                >
                    Get Tickets →
                </a>
            </div>
        </div>
    );
};

const CalendarEventItem = ({ festival }) => {
    const iconColor = festival.place.includes('대학교') ? '#5cb85c' : '#f0ad4e'; 
    const dateRange = festival.start_date === festival.end_date
        ? formatDate(festival.start_date)
        : `${formatDate(festival.start_date)} ~ ${formatDate(festival.end_date)}`;

    return (
        <div className="calendar-event-item">
            <span className="event-icon" style={{ backgroundColor: iconColor }}></span>
            <span className="event-title">{festival.title}</span>
            <span className="event-date">{dateRange}</span>
        </div>
    );
};

function KpopFestivalPage({ isEmbedded }) {
    const [festivals, setFestivals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [calendarDate, setCalendarDate] = useState(new Date()); 
    const [searchTerm, setSearchTerm] = useState(''); 

    const containerStyle = isEmbedded ? { 
        padding: '20px', minHeight: '100%', maxWidth: 'none', margin: 0, backgroundColor: 'transparent'
    } : {};
    
    const [currentPage, setCurrentPage] = useState(1); 
    const itemsPerPage = 5; 
    
    useEffect(() => {
        const fetchFestivals = async () => {
            try {
                const response = await api.get('/api/festivals');
                setFestivals(response.data);
                setLoading(false);
            } catch (err) {
                console.error("데이터 로딩 실패:", err);
                setError("콘서트/축제 데이터를 불러오는 데 실패했습니다.");
                setLoading(false);
            }
        };
        fetchFestivals();
    }, []);
    
    useEffect(() => {
        setCurrentPage(1);
    }, [searchTerm]);

    const filteredByCalendar = useMemo(() => {
        if (!calendarDate) return [];

        const selectedDate = new Date(calendarDate);
        selectedDate.setHours(0, 0, 0, 0);

        return festivals.filter(festival => {
            const start = new Date(festival.start_date);
            const end = new Date(festival.end_date);
            
            start.setHours(0, 0, 0, 0);
            end.setHours(0, 0, 0, 0);

            return selectedDate >= start && selectedDate <= end;
        });
    }, [festivals, calendarDate]);

    const { currentItems, totalPages, displayPageNumbers, filteredFestivals } = useMemo(() => {
        const filtered = festivals.filter(festival => 
            festival.title.toLowerCase().includes(searchTerm.toLowerCase())
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
        for (let i = startPage; i <= endPage; i++) {
            displayPageNumbers.push(i);
        }

        return { currentItems, totalPages, displayPageNumbers, filteredFestivals: filtered }; 
    }, [festivals, currentPage, itemsPerPage, searchTerm]);

    const handlePageChange = (pageNumber) => {
        setCurrentPage(pageNumber);
    };

    const handleSearchChange = (event) => {
        setSearchTerm(event.target.value);
    };

    const tileContent = ({ date, view }) => {
        if (view === 'month') {
            const dateStr = formatDate(date);
            
            const hasEvent = festivals.some(festival => {
                const start = new Date(festival.start_date);
                const end = new Date(festival.end_date);
                const current = new Date(dateStr);

                start.setHours(0, 0, 0, 0);
                end.setHours(0, 0, 0, 0);
                current.setHours(0, 0, 0, 0);

                return current >= start && current <= end;
            });

            if (hasEvent) {
                return <div className="event-dot"></div>;
            }
        }
        return null;
    };

    if (loading) {
        return <div className="kpop-festival-page" style={containerStyle}>로딩 중...</div>;
    }
    
    if (error) {
        return <div className="kpop-festival-page error" style={containerStyle}>오류: {error}</div>;
    }

    return (
        <div className="kpop-festival-page" style={containerStyle}>
            <header className="page-header">
                <h1>K-POP Festival & Concert List</h1>
            </header>

            <div className="content-wrapper">
                <div className="calendar-side-wrapper"> 
                    <section className="calendar-section">
                        <div className="calendar-box">
                            <Calendar
                                onChange={setCalendarDate}
                                value={calendarDate}
                                tileContent={tileContent} 
                                locale="ko-KR"
                                formatDay={(locale, date) => date.toLocaleString("en", { day: "numeric" })}
                            />
                        </div>
                    </section>
                    
                    <section className="calendar-events-section">
                        <h2 className="calendar-events-title">
                            {formatDate(calendarDate)} ({filteredByCalendar.length}건)
                        </h2>
                        
                        <div className="calendar-events-list">
                            {filteredByCalendar.length > 0 ? (
                                filteredByCalendar.map((festival) => (
                                    <CalendarEventItem key={festival.id} festival={festival} />
                                ))
                            ) : (
                                <p className="no-events-message">선택된 날짜에 예정된 축제가 없습니다.</p>
                            )}
                        </div>
                    </section>
                </div>
                
                <section className="festival-list-section">
                    <div className="festival-header-wrapper">
                        <h2>K-concert information 🧐</h2>
                        
                        <div className="festival-search-bar">
                            <input
                                type="text"
                                placeholder="Search for the title of the concert      🔎"
                                value={searchTerm}
                                onChange={handleSearchChange}
                            />
                        </div>
                    </div>
                    
                    {currentItems.length > 0 ? (
                        <>
                            <div className="festival-cards-grid">
                                {currentItems.map((festival) => (
                                    <FestivalCard key={festival.id} festival={festival} />
                                ))}
                            </div>

                            {totalPages > 1 && (
                                <div className="pagination-controls">
                                    {displayPageNumbers.map(number => (
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
                        <p className="no-data-message">
                            {searchTerm ? '검색 결과가 없습니다.' : '현재 등록된 축제/콘서트 정보가 없습니다.'}
                        </p>
                    )}
                </section>
            </div>
        </div>
    );
}

export default KpopFestivalPage;
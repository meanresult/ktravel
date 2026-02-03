import React, { useState, useEffect } from 'react';
import '../styles/FestivalPage.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function FestivalPage() {
    const [festivals, setFestivals] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchFestivals();
    }, []);

    const fetchFestivals = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_URL}/api/festivals/`, {
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                setFestivals(data);
            }
        } catch (error) {
            console.error('Error fetching festivals:', error);
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('ko-KR');
    };

    if (loading) {
        return (
            <div className="festival-page">
                <div className="loading">Loading...</div>
            </div>
        );
    }

    return (
        <div className="festival-page">
            <header className="festival-header">
                <h1>🎉 Korean Festivals</h1>
                <p>총 {festivals.length}개의 축제</p>
            </header>

            <div className="festival-grid">
                {festivals.map((festival) => (
                    <div key={festival.fastival_id} className="festival-card">
                        <div className="festival-image">
                            {festival.image_url ? (
                                <img src={festival.image_url} alt={festival.title} />
                            ) : (
                                <div className="no-image">🎪</div>
                            )}
                        </div>

                        <div className="festival-info">
                            <h3>{festival.title}</h3>
                            
                            <div className="festival-dates">
                                📅 {formatDate(festival.start_date)} ~ {formatDate(festival.end_date)}
                            </div>

                            {festival.description && (
                                <p className="festival-description">
                                    {festival.description}
                                </p>
                            )}

                            {festival.latitude && festival.longitude && (
                                <div className="festival-location">
                                    📍 {festival.latitude}, {festival.longitude}
                                </div>
                            )}

                            {festival.detail_url && (
                                <a
                                    href={festival.detail_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="btn-detail"
                                >
                                    상세보기
                                </a>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default FestivalPage;
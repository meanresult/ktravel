import React from 'react';
import KDH_ChatbotPage from './KDH_ChatbotPage';  // ← 같은 폴더
import NaverMap from './NaverMap'; 

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function KDH_ChatbotMapLayout() {
    return (
        <div style={styles.layoutContainer}>
            {/* 1. 챗봇 영역 (왼쪽) */}
            <div style={styles.chatArea}>
                <KDH_ChatbotPage />
            </div>

            {/* 2. 지도 영역 (오른쪽) */}
            <div style={styles.mapArea}>
                <NaverMap />
            </div>
        </div>
    );
}

const styles = {
    layoutContainer: {
        display: 'flex',
        height: '100vh',
        width: '100vw'
    },
    chatArea: {
        flexBasis: '50%',
        minWidth: '400px',
        overflow: 'hidden',
        position: 'relative',
        height: '100%'
    },
    mapArea: {
        flexBasis: '50%',
        position: 'relative',
        height: '100%'
    }
};

export default KDH_ChatbotMapLayout;
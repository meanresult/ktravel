import React from 'react';
// 기존 챗봇 컴포넌트를 가져옵니다.
import Kpop_ChatbotPage from './Kpop_ChatbotPage';
// 새로 만든 네이버맵 컴포넌트를 가져옵니다.
import NaverMap from './NaverMap'; // 파일명이 NAVERMap이면 맞춰서 수정해줘!

function Kpop_ChatbotMapLayout() {
    return (
        // Flexbox를 사용하여 두 영역을 나란히 배치합니다.
        <div style={styles.layoutContainer}>
            
            {/* 1. 챗봇 영역 (왼쪽) */}
            <div style={styles.chatArea}>
                {/* isEmbedded prop은 내부 UI 높이를 줄이기 용도로 전달 */}
                <Kpop_ChatbotPage isEmbedded={true} />
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
        flexBasis: '50%', // 50% 너비
        minWidth: '400px',
        overflow: 'hidden',
        position: 'relative',
        height: '100%' // 추가해도 됨
    },
    mapArea: {
        flexBasis: '50%', // 50% 너비
        position: 'relative',
        height: '100%' // 필수!
    }
};

export default Kpop_ChatbotMapLayout;

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/common/Header';
import ChatContainer from '../components/chat/ChatContainer';
import DestinationList from '../components/destinations/DestinationList';
import Loading from '../components/common/Loading';
import authService from '../services/authService';
import './DashboardPage.css';

function DashboardPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshDestinations, setRefreshDestinations] = useState(0);

  useEffect(() => {
    // 사용자 정보 확인
    const checkAuth = async () => {
      try {
        const userData = await authService.getMe();
        setUser(userData);
      } catch (error) {
        // 인증 실패 시 로그인 페이지로
        navigate('/login');
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, [navigate]);

  // 여행지 목록 새로고침 트리거
  const handleDestinationsUpdate = () => {
    setRefreshDestinations((prev) => prev + 1);
  };

  if (loading) {
    return <Loading message="로딩 중..." />;
  }

  return (
    <div className="dashboard">
      <Header user={user} />
      
      <div className="dashboard-content">
        <div className="chat-section">
          <ChatContainer onDestinationsUpdate={handleDestinationsUpdate} />
        </div>
        
        <div className="sidebar-section">
          <DestinationList refreshTrigger={refreshDestinations} />
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;

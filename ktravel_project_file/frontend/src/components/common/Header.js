import React from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../../services/authService';
import './Header.css';

function Header({ user }) {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await authService.logout();
      navigate('/login');
    } catch (error) {
      console.error('로그아웃 실패:', error);
      // 실패해도 로그인 페이지로 이동
      navigate('/login');
    }
  };

  return (
    <header className="header">
      <div className="header-content">
        <h1 className="header-title">🌍 Travel Planner</h1>
        {user && (
          <div className="header-user">
            <span className="user-name">{user.name}님</span>
            <button onClick={handleLogout} className="btn-logout">
              로그아웃
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

export default Header;

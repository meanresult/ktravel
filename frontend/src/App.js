import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import DashboardPage from './pages/DashboardPage';
import Concept_MainPage from './pages/Concept_MainPage.jsx';
import Concept_LoginPage from './pages/Concept_LoginPage.jsx';
import KpopFestival_MapLayout from './pages/KpopFestival_MapLayout.jsx';
import KDH_ChatbotMapLayout from './pages/KDH_ChatbotMapLayout.jsx';
import FestivalPage from './pages/FestivalPage.jsx';
console.log('CLIENT_ID:', process.env.REACT_APP_NAVER_MAPS_CLIENT_ID);


function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* 기존 라우트 - 여행 플래너 대시보드 */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />

                      {/* 로그인 페이지 */}
          

          {/* 신규 라우트 - K-Guidance 기능 */}
          <Route path="/" element={<Concept_MainPage />} />
          <Route path="/festival" element={<KpopFestival_MapLayout />} />
          
          <Route path="/chatbot/demon-hunters" element={<KDH_ChatbotMapLayout />} />
          <Route path="/festivals" element={<FestivalPage />} />

          {/* 404 처리 */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
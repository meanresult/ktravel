import React from 'react';
import './Loading.css';

function Loading({ message = '로딩 중...' }) {
  return (
    <div className="loading-container">
      <div className="spinner"></div>
      <p className="loading-message">{message}</p>
    </div>
  );
}

export default Loading;

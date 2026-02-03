import React from 'react';
import './ErrorMessage.css';

function ErrorMessage({ message, onClose }) {
  if (!message) return null;

  return (
    <div className="error-message">
      <span>{message}</span>
      {onClose && (
        <button onClick={onClose} className="error-close">
          ✕
        </button>
      )}
    </div>
  );
}

export default ErrorMessage;

import React, { useState } from 'react';

function ChatInput({ onSend, disabled }) {
    const [message, setMessage] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (message.trim() && !disabled) {
            onSend(message);
            setMessage('');
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    return (
        <div className="input-bar">
            <input
                type="text"
                placeholder="Tell me the route of the main Korean travel destinations..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={disabled}
            />
            <span 
                className="search-icon"
                onClick={handleSubmit}
                style={{ cursor: disabled ? 'not-allowed' : 'pointer' }}
            >
                🔍
            </span>
        </div>
    );
}

export default ChatInput;
// ConceptMainPage.jsx (로직과 구조 전용) - 인증 방식 수정됨

import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import '../styles/Concept_MainPage.css'; // 외부 CSS 파일만 import
import { FaMicrophone, FaStar, FaHamburger } from 'react-icons/fa';
import Sidebar from '../components/Sidebar';


const ConceptCard = ({ title, subTitle, icon: Icon, colorClass, destination }) => (
    <Link 
        to={destination}
        // 배경, hover 효과를 담당하는 클래스를 Link에 적용
        className={`concept-card-link ${colorClass}`} 
    >
        <div className="concept-card-content"> 
            <h3 className="card-title">{title}</h3>
            <p className="card-subtitle">{subTitle}</p>
            <div className="card-icon-wrapper">
                <Icon className="card-icon" />
                <span className="arrow">→</span>
            </div>
        </div>
    </Link>
);

const ConceptMainPage = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        username: '',
        password: '',
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [rememberMe, setRememberMe] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [currentUser, setCurrentUser] = useState(null);

    // ************************
    // 로그인/상태 관리 로직
    // ************************
    useEffect(() => {
        checkLoginStatus();
    }, []);

    const checkLoginStatus = async () => {
        try {
            const sessionId = localStorage.getItem('session_id');
            if (!sessionId) {
                setIsLoggedIn(false);
                return;
            }

            const response = await fetch('http://localhost:8000/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${sessionId}`
                }
            });

            if (response.ok) {
                const userData = await response.json();
                setIsLoggedIn(true);
                setCurrentUser(userData);
            } else {
                // 세션이 만료되었거나 유효하지 않음
                localStorage.removeItem('session_id');
                setIsLoggedIn(false);
            }
        } catch (err) {
            localStorage.removeItem('session_id');
            setIsLoggedIn(false);
        }
    };

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value,
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const response = await fetch('http://localhost:8000/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: formData.username,
                    password: formData.password,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Login failed');
            }

            const responseData = await response.json();
            
            // session_id를 localStorage에 저장
            if (responseData.session_id) {
                localStorage.setItem('session_id', responseData.session_id);
                
                if (rememberMe) {
                    localStorage.setItem('user', JSON.stringify(responseData.user));
                }

                setIsLoggedIn(true);
                setCurrentUser(responseData.user);
                setFormData({ username: '', password: '' });
            } else {
                throw new Error('로그인 응답에 session_id가 없습니다.');
            }
        } catch (err) {
            setError(err.message || 'An error occurred during login');
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = async () => {
        try {
            const sessionId = localStorage.getItem('session_id');
            
            if (sessionId) {
                await fetch('http://localhost:8000/api/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${sessionId}`
                    }
                });
            }

            localStorage.removeItem('session_id');
            localStorage.removeItem('user');
            setIsLoggedIn(false);
            setCurrentUser(null);
        } catch (err) {
            console.error('Logout error:', err);
            // 에러가 나도 로컬 상태는 정리
            localStorage.removeItem('session_id');
            localStorage.removeItem('user');
            setIsLoggedIn(false);
            setCurrentUser(null);
        }
    };
    // ************************
    
    return (
        <>
            {/* Sidebar는 컴포넌트 내부에서 위치를 잡습니다. */}
            {isLoggedIn && <Sidebar />}
            
            {/* 인라인 스타일 제거: .login-page-container 클래스에 transition 및 margin-left 속성 적용 */}
            <div className="login-page-container">
                
                <div className="main-content-area">
                    <header className="page-header">
                        <h1 className="header-title">K-Guidance</h1>
                        
                        {/* 로그인 후 사용자 정보: 인라인 스타일 제거, 클래스 적용 */}
                        {isLoggedIn && currentUser && (
                            <div className="user-info-display">
                                <span className="user-text">
                                    👤 {currentUser.username || currentUser.name}
                                </span>
                                <button
                                    onClick={handleLogout}
                                    className="logout-button"
                                >
                                    Logout
                                </button>
                            </div>
                        )}
                    </header>

                    <section className="welcome-section">
                        <h2 className="welcome-title">We are K-Guidance,</h2>
                        
                        <p className="welcome-text">
                            We serve as your personalized travel planner for foreign visitors, ensuring you never lose your way amidst Korea's diverse charms.
                            Don't get lost in a sea of complex information.
                        </p>

                        <p className="welcome-text">
                            Based on the single concept you choose, we instantly recommend the trendiest and most meaningful destinations.
                        </p>

                        <p className="welcome-text">
                            Using the recommended itinerary as a foundation, freely adjust the travel route and timing to perfectly match your preferences, creating a one-of-a-kind, perfect Korean travel plan.
                        </p>

                        <p className="welcome-text">
                            Decide on your concept right now and start your most enjoyable trip to Korea!
                        </p>
                    </section>

                    <section className="concept-selection">
                        <h3 className="concept-prompt"> Please decide the concept ✔</h3>
                        <div className="concept-cards-grid">
                            <ConceptCard 
                                title="K-POP DEMON HUNTERS" 
                                subTitle="Dive into the world of K-Pop and fantasy."
                                icon={FaMicrophone} 
                                colorClass="card-kpop-demon"
                                destination="/chatbot/demon-hunters"
                            />
                            <ConceptCard 
                                title="K-POP STAR" 
                                subTitle="Experience the glamorous life of a K-Pop idol."
                                icon={FaStar} 
                                colorClass="card-kpop-star"
                                destination="/chatbot/kpop-star"
                            />
                            <ConceptCard 
                                title="K-FOOD" 
                                subTitle="Explore Korea through its delicious culinary journey."
                                icon={FaHamburger} 
                                colorClass="card-kfood"
                                destination="/chatbot/k-food"
                            />
                        </div>
                    </section>
                </div>

                {/* Login Form (오른쪽 영역) - 로그인 전에만 표시 */}
                {!isLoggedIn && (
                    <div className="login-form-sidebar">
                        <div className="login-box">
                            <h2 className="login-title">✈ Sign In</h2>
                            <p className="login-subtitle">Join your K-Experience journey</p>
                            
                            {/* 에러 메시지: 인라인 스타일 제거, 클래스 적용 */}
                            {error && (
                                <div className="error-message-box">
                                    <span>{error}</span>
                                    <button 
                                        onClick={() => setError('')}
                                        className="error-close-button"
                                    >
                                        &times;
                                    </button>
                                </div>
                            )}
                            
                            <form className="login-form" onSubmit={handleSubmit}>
                                <label htmlFor="username">User ID</label>
                                <input 
                                    type="text" 
                                    id="username"
                                    name="username"
                                    placeholder="Enter your username" 
                                    value={formData.username}
                                    onChange={handleChange}
                                    className="text-input"
                                    required
                                    autoComplete="username"
                                />
                                
                                <label htmlFor="password">Password</label>
                                <div className="password-input-wrapper">
                                    <input 
                                        type={showPassword ? "text" : "password"}
                                        id="password"
                                        name="password"
                                        placeholder="••••••••••" 
                                        value={formData.password}
                                        onChange={handleChange}
                                        className="text-input"
                                        required
                                        autoComplete="current-password"
                                    />
                                    <span 
                                        className="password-toggle"
                                        onClick={() => setShowPassword(!showPassword)}
                                    >
                                        {showPassword ? '🙈' : '👁️'}
                                    </span>
                                </div>

                                <div className="remember-forgot">
                                    <label className="checkbox-container">
                                        <input 
                                            type="checkbox" 
                                            checked={rememberMe}
                                            onChange={(e) => setRememberMe(e.target.checked)}
                                        />
                                        <span className="checkmark"></span>
                                        Remember me
                                    </label>
                                    <Link to="/forgot-password" className="forgot-password">Forgot?</Link>
                                </div>
                                
                                <button 
                                    type="submit" 
                                    className="sign-in-button"
                                    disabled={loading}
                                    // 로딩 중 스타일은 CSS 파일의 .sign-in-button:disabled에서 처리
                                >
                                    {loading ? 'Signing In...' : 'Sign In'}
                                </button>
                            </form>

                            <div className="social-login-divider"></div>
                            
                            <div className="sign-up-prompt">
                                Don't have an account? <Link to="/signup" className="sign-up-link">Sign up</Link>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </>
    );
};

export default ConceptMainPage;
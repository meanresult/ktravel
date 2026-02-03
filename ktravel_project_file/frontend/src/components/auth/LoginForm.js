import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import authService from '../../services/authService';
import ErrorMessage from '../common/ErrorMessage';
import './AuthForms.css';

function LoginForm() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

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
        // authService 사용 (이미 session_id 저장 로직 포함)
        const response = await authService.login(formData.username, formData.password);
        
        // 로그인 성공 시 메인 페이지로 이동
        navigate('/');
        
    } catch (error) {
        console.error('Login error:', error);
        setError(error.message || '로그인에 실패했습니다.');
    } finally {
        setLoading(false);
    }
};

  return (
    <div className="auth-container">
      <div className="auth-box">
        <h1 className="auth-title">✈ K-Guidance</h1>
        <h2 className="auth-subtitle">Login</h2>

        <ErrorMessage message={error} onClose={() => setError('')} />

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label>User ID</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              placeholder="Please enter your ID"
              required
            />
          </div>

          <div className="form-group">
            <label>Passward</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Passward"
              required
            />
          </div>

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Signing up...' : 'Done signing up!'}
          </button>
        </form>

        <p className="auth-footer">
          Do you already have an account? <Link to="/signup">Sign Up</Link>
        </p>
      </div>
    </div>
  );
}

export default LoginForm;

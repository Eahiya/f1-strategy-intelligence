/**
 * F1 Strategy Intelligence System - Security Layer v3.1
 * Login Page Component
 * 
 * Secure login interface with role-based access information.
 */
import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Shield, User, Lock, AlertCircle, CheckCircle } from 'lucide-react';

const LoginPage = ({ onLoginSuccess }) => {
  const { login, error } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');
    setLoading(true);

    if (!username || !password) {
      setLocalError('Please enter both username and password');
      setLoading(false);
      return;
    }

    const result = await login(username, password);
    
    if (result.success) {
      onLoginSuccess?.();
    } else {
      setLocalError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        {/* Header */}
        <div className="login-header">
          <Shield className="login-icon" size={48} />
          <h1>F1 Strategy Intelligence</h1>
          <p className="login-subtitle">Elite Edition v3.1</p>
          <div className="security-badge">
            <CheckCircle size={14} />
            <span>Secure Access</span>
          </div>
        </div>

        {/* Error Display */}
        {(error || localError) && (
          <div className="error-banner">
            <AlertCircle size={18} />
            <span>{error || localError}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">
              <User size={16} />
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
              disabled={loading}
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">
              <Lock size={16} />
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Authenticating...
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        {/* Role Information */}
        <div className="role-info">
          <h3>Access Levels</h3>
          <div className="role-grid">
            <div className="role-card admin">
              <div className="role-badge">ADMIN</div>
              <p>Full system access<br/>User management<br/>All simulations</p>
            </div>
            <div className="role-card engineer">
              <div className="role-badge">ENGINEER</div>
              <p>Elite AI tools<br/>Digital twin<br/>Optimization</p>
            </div>
            <div className="role-card viewer">
              <div className="role-badge">VIEWER</div>
              <p>Read-only access<br/>View simulations<br/>Basic analysis</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="login-footer">
          <p>Protected by JWT Authentication & RBAC</p>
          <p className="version">v3.1.0 Security Layer</p>
        </div>
      </div>

      {/* Styles */}
      <style>{`
        .login-container {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #0f0f0f 0%, #1a1a2e 50%, #16213e 100%);
          padding: 20px;
        }

        .login-card {
          width: 100%;
          max-width: 480px;
          background: rgba(20, 20, 30, 0.95);
          border-radius: 16px;
          border: 1px solid rgba(225, 6, 0, 0.3);
          padding: 40px;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }

        .login-header {
          text-align: center;
          margin-bottom: 30px;
        }

        .login-icon {
          color: #e10600;
          margin-bottom: 16px;
        }

        .login-header h1 {
          color: #fff;
          font-size: 24px;
          font-weight: 700;
          margin: 0 0 8px 0;
        }

        .login-subtitle {
          color: #888;
          font-size: 14px;
          margin: 0 0 12px 0;
        }

        .security-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          background: rgba(0, 255, 100, 0.1);
          color: #00ff64;
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
        }

        .error-banner {
          display: flex;
          align-items: center;
          gap: 10px;
          background: rgba(225, 6, 0, 0.1);
          border: 1px solid rgba(225, 6, 0, 0.3);
          color: #ff6666;
          padding: 12px 16px;
          border-radius: 8px;
          margin-bottom: 20px;
          font-size: 14px;
        }

        .login-form {
          margin-bottom: 30px;
        }

        .form-group {
          margin-bottom: 20px;
        }

        .form-group label {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #aaa;
          font-size: 14px;
          margin-bottom: 8px;
        }

        .form-group input {
          width: 100%;
          padding: 12px 16px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          color: #fff;
          font-size: 16px;
          transition: all 0.2s;
        }

        .form-group input:focus {
          outline: none;
          border-color: #e10600;
          background: rgba(225, 6, 0, 0.05);
        }

        .form-group input:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .login-button {
          width: 100%;
          padding: 14px;
          background: linear-gradient(135deg, #e10600 0%, #ff3300 100%);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
        }

        .login-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(225, 6, 0, 0.4);
        }

        .login-button:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .spinner {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .role-info {
          margin-bottom: 20px;
        }

        .role-info h3 {
          color: #888;
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 1px;
          margin-bottom: 12px;
          text-align: center;
        }

        .role-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 10px;
        }

        .role-card {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          padding: 12px;
          text-align: center;
        }

        .role-card.admin {
          border-color: rgba(225, 6, 0, 0.3);
        }

        .role-card.engineer {
          border-color: rgba(255, 193, 7, 0.3);
        }

        .role-card.viewer {
          border-color: rgba(100, 200, 255, 0.3);
        }

        .role-badge {
          font-size: 10px;
          font-weight: 700;
          letter-spacing: 1px;
          margin-bottom: 8px;
          padding: 2px 6px;
          border-radius: 4px;
          display: inline-block;
        }

        .admin .role-badge {
          background: rgba(225, 6, 0, 0.2);
          color: #ff6666;
        }

        .engineer .role-badge {
          background: rgba(255, 193, 7, 0.2);
          color: #ffc107;
        }

        .viewer .role-badge {
          background: rgba(100, 200, 255, 0.2);
          color: #64c8ff;
        }

        .role-card p {
          color: #888;
          font-size: 11px;
          line-height: 1.4;
          margin: 0;
        }

        .login-footer {
          text-align: center;
          padding-top: 20px;
          border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .login-footer p {
          color: #666;
          font-size: 12px;
          margin: 0;
        }

        .login-footer .version {
          color: #444;
          font-size: 11px;
          margin-top: 4px;
        }
      `}</style>
    </div>
  );
};

export default LoginPage;

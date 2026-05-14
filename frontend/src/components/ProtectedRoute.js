/**
 * F1 Strategy Intelligence System - Security Layer v3.1
 * Protected Route Component
 * 
 * Route guard that enforces authentication and role-based access.
 */
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, AlertTriangle } from 'lucide-react';

const ProtectedRoute = ({ 
  children, 
  requiredRoles = null,
  fallback = null 
}) => {
  const { user, loading, isAuthenticated } = useAuth();

  // Show loading while checking auth
  if (loading) {
    return (
      <div className="loading-auth">
        <div className="spinner"></div>
        <p>Verifying access...</p>
        <style>{`
          .loading-auth {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 400px;
            color: #888;
          }
          .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(225, 6, 0, 0.3);
            border-top-color: #e10600;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 16px;
          }
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  // Not authenticated - redirect to login
  if (!isAuthenticated) {
    return fallback || <Navigate to="/login" replace />;
  }

  // Check role requirements
  if (requiredRoles) {
    const roles = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles];
    const hasRequiredRole = roles.includes(user?.role);

    if (!hasRequiredRole) {
      return (
        <div className="access-denied">
          <Shield size={48} className="shield-icon" />
          <h2>Access Denied</h2>
          <p>
            <AlertTriangle size={16} />
            You don't have permission to access this resource.
          </p>
          <div className="role-info">
            <p>Your role: <strong>{user?.role}</strong></p>
            <p>Required: <strong>{roles.join(' or ')}</strong></p>
          </div>
          <button onClick={() => window.history.back()}>
            Go Back
          </button>
          <style>{`
            .access-denied {
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              min-height: 400px;
              padding: 40px;
              text-align: center;
            }
            .shield-icon {
              color: #e10600;
              margin-bottom: 20px;
            }
            .access-denied h2 {
              color: #fff;
              margin: 0 0 12px 0;
            }
            .access-denied p {
              color: #888;
              display: flex;
              align-items: center;
              gap: 8px;
              margin-bottom: 20px;
            }
            .role-info {
              background: rgba(255, 255, 255, 0.05);
              padding: 16px 24px;
              border-radius: 8px;
              margin-bottom: 20px;
            }
            .role-info p {
              margin: 4px 0;
              font-size: 14px;
            }
            .access-denied button {
              padding: 10px 20px;
              background: rgba(255, 255, 255, 0.1);
              color: #fff;
              border: 1px solid rgba(255, 255, 255, 0.2);
              border-radius: 6px;
              cursor: pointer;
              transition: all 0.2s;
            }
            .access-denied button:hover {
              background: rgba(255, 255, 255, 0.2);
            }
          `}</style>
        </div>
      );
    }
  }

  // All checks passed - render children
  return children;
};

export default ProtectedRoute;

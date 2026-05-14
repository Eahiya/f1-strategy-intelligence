/**
 * F1 Strategy Platform v4.0 - Offline Indicator
 * Shows network status and offline mode
 */
import React, { useState, useEffect } from 'react';
import { WifiOff, RefreshCw, AlertCircle } from 'lucide-react';

const OfflineIndicator = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [showRetry, setShowRetry] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setShowRetry(false);
    };
    
    const handleOffline = () => {
      setIsOnline(false);
      setShowRetry(true);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const handleRetry = () => {
    window.location.reload();
  };

  if (isOnline) return null;

  return (
    <div className="offline-indicator">
      <div className="offline-content">
        <WifiOff size={48} className="offline-icon" />
        <h2 className="offline-title">You're Offline</h2>
        <p className="offline-message">
          Check your connection and try again.
        </p>
        
        {showRetry && (
          <button className="retry-btn" onClick={handleRetry}>
            <RefreshCw size={18} />
            Retry Connection
          </button>
        )}
        
        <div className="offline-features">
          <p className="offline-features-title">
            <AlertCircle size={14} />
            Available Offline:
          </p>
          <ul>
            <li>View cached simulations</li>
            <li>Previously loaded strategies</li>
            <li>Circuit information</li>
          </ul>
        </div>
      </div>
      
      <style>{`
        .offline-indicator {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(10, 10, 15, 0.98);
          z-index: 9999;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
        }
        
        .offline-content {
          text-align: center;
          max-width: 300px;
        }
        
        .offline-icon {
          color: #ff6666;
          margin-bottom: 16px;
        }
        
        .offline-title {
          font-size: 24px;
          font-weight: 700;
          margin: 0 0 8px 0;
        }
        
        .offline-message {
          color: #888;
          margin: 0 0 24px 0;
        }
        
        .retry-btn {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          background: #e10600;
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 8px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          margin-bottom: 32px;
        }
        
        .offline-features {
          background: rgba(255, 255, 255, 0.05);
          padding: 16px;
          border-radius: 8px;
          text-align: left;
        }
        
        .offline-features-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 12px;
          color: #888;
          text-transform: uppercase;
          margin: 0 0 12px 0;
        }
        
        .offline-features ul {
          margin: 0;
          padding-left: 20px;
          color: #aaa;
          font-size: 14px;
          line-height: 1.8;
        }
      `}</style>
    </div>
  );
};

export default OfflineIndicator;

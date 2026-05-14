/**
 * F1 Strategy Platform v4.0 - Elite AI View
 * Responsive elite features interface
 */
import React, { useState } from 'react';
import { Zap, Brain, Users, ChevronRight } from 'lucide-react';

const EliteView = ({ deviceType, api, user }) => {
  const [activeFeature, setActiveFeature] = useState(null);

  const features = [
    {
      id: 'rl',
      title: 'RL Strategy Engine',
      description: 'AI-powered real-time decisions',
      icon: Brain,
      role: 'engineer',
      available: ['admin', 'engineer'].includes(user?.role)
    },
    {
      id: 'opponent',
      title: 'Opponent Analysis',
      description: 'Game theory & undercut detection',
      icon: Users,
      role: 'engineer',
      available: ['admin', 'engineer'].includes(user?.role)
    },
    {
      id: 'risk',
      title: 'Risk Assessment',
      description: 'Probabilistic modeling',
      icon: Zap,
      role: 'viewer',
      available: true
    }
  ];

  const handleFeatureClick = (feature) => {
    if (!feature.available) {
      alert('This feature requires Engineer or Admin access');
      return;
    }
    setActiveFeature(feature.id);
  };

  return (
    <div className="elite-view">
      <h1 className="page-title">Elite AI Features</h1>
      
      <p className="elite-subtitle">
        Advanced AI-powered strategy tools. Some features require elevated permissions.
      </p>

      <div className={`elite-grid ${deviceType}`}>
        {features.map((feature) => (
          <div
            key={feature.id}
            className={`elite-card ${!feature.available ? 'locked' : ''} ${activeFeature === feature.id ? 'active' : ''}`}
            onClick={() => handleFeatureClick(feature)}
          >
            <div className="elite-card-header">
              <div className={`elite-icon ${feature.available ? '' : 'locked'}`}>
                <feature.icon size={24} />
              </div>
              {!feature.available && (
                <span className="role-badge">{feature.role}+</span>
              )}
            </div>
            
            <h3 className="elite-card-title">{feature.title}</h3>
            <p className="elite-card-desc">{feature.description}</p>
            
            <div className="elite-card-footer">
              <span className="elite-action">
                {feature.available ? 'Open' : 'Locked'}
                <ChevronRight size={16} />
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Feature Placeholder Content */}
      {activeFeature && (
        <div className="feature-content animate-slide-up">
          <button 
            className="back-btn"
            onClick={() => setActiveFeature(null)}
          >
            ← Back to Features
          </button>
          
          <div className="feature-placeholder">
            <h2>{features.find(f => f.id === activeFeature)?.title}</h2>
            <p>This feature is coming soon in the mobile app.</p>
            <p>Use the desktop version for full functionality.</p>
          </div>
        </div>
      )}

      <style>{`
        .elite-view {
          padding-bottom: 80px;
        }
        
        .page-title {
          font-size: 24px;
          font-weight: 700;
          margin: 0 0 8px 0;
        }
        
        .elite-subtitle {
          color: #888;
          font-size: 14px;
          margin: 0 0 24px 0;
        }
        
        .elite-grid {
          display: grid;
          gap: 16px;
          grid-template-columns: 1fr;
        }
        
        @media (min-width: 768px) {
          .elite-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }
        
        @media (min-width: 1024px) {
          .elite-grid {
            grid-template-columns: repeat(3, 1fr);
          }
        }
        
        .elite-card {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 16px;
          padding: 20px;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .elite-card:active {
          transform: scale(0.98);
        }
        
        .elite-card.locked {
          opacity: 0.6;
          cursor: not-allowed;
        }
        
        .elite-card.active {
          border-color: #e10600;
          background: rgba(225, 6, 0, 0.05);
        }
        
        .elite-card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }
        
        .elite-icon {
          width: 48px;
          height: 48px;
          background: linear-gradient(135deg, #e10600 0%, #ff3300 100%);
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
        }
        
        .elite-icon.locked {
          background: rgba(255, 255, 255, 0.1);
        }
        
        .role-badge {
          font-size: 10px;
          text-transform: uppercase;
          background: rgba(255, 193, 7, 0.2);
          color: #ffc107;
          padding: 4px 8px;
          border-radius: 4px;
        }
        
        .elite-card-title {
          font-size: 18px;
          font-weight: 600;
          margin: 0 0 8px 0;
        }
        
        .elite-card-desc {
          color: #888;
          font-size: 14px;
          margin: 0 0 16px 0;
        }
        
        .elite-card-footer {
          display: flex;
          justify-content: flex-end;
        }
        
        .elite-action {
          display: flex;
          align-items: center;
          gap: 4px;
          color: #e10600;
          font-size: 14px;
          font-weight: 600;
        }
        
        .feature-content {
          margin-top: 24px;
        }
        
        .back-btn {
          background: rgba(255, 255, 255, 0.1);
          border: none;
          color: #fff;
          padding: 12px 16px;
          border-radius: 8px;
          cursor: pointer;
          margin-bottom: 16px;
        }
        
        .feature-placeholder {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 16px;
          padding: 40px;
          text-align: center;
        }
        
        .feature-placeholder h2 {
          margin: 0 0 16px 0;
        }
        
        .feature-placeholder p {
          color: #888;
          margin: 0 0 8px 0;
        }
      `}</style>
    </div>
  );
};

export default EliteView;

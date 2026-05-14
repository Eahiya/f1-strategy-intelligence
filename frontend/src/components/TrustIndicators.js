/**
 * F1 Strategy Platform v6.0 - Trust Indicators
 * Displays confidence metrics and simple explanations for users.
 */
import React from 'react';
import { Shield, Database, Brain, AlertTriangle, CheckCircle } from 'lucide-react';

const TrustScore = ({ label, score, icon: Icon, color = "green" }) => {
  const colors = {
    green: "#00ff64",
    yellow: "#ffc107",
    red: "#ff6666"
  };
  
  const getColor = (s) => {
    if (s >= 80) return colors.green;
    if (s >= 60) return colors.yellow;
    return colors.red;
  };
  
  const displayColor = color === "auto" ? getColor(score) : colors[color];
  
  return (
    <div className="trust-score">
      <div className="trust-icon" style={{ color: displayColor }}>
        <Icon size={20} />
      </div>
      <div className="trust-info">
        <span className="trust-label">{label}</span>
        <div className="trust-bar-container">
          <div 
            className="trust-bar" 
            style={{ 
              width: `${score}%`,
              background: displayColor
            }} 
          />
        </div>
        <span className="trust-value">{score}%</span>
      </div>
      
      <style>{`
        .trust-score {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 8px;
          margin-bottom: 8px;
        }
        
        .trust-icon {
          flex-shrink: 0;
        }
        
        .trust-info {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        
        .trust-label {
          font-size: 12px;
          color: #888;
          text-transform: uppercase;
        }
        
        .trust-bar-container {
          height: 4px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 2px;
          overflow: hidden;
        }
        
        .trust-bar {
          height: 100%;
          border-radius: 2px;
          transition: width 0.3s ease;
        }
        
        .trust-value {
          font-size: 14px;
          font-weight: 600;
          color: #fff;
        }
      `}</style>
    </div>
  );
};

export const TrustPanel = ({ 
  dataConfidence = 85,
  modelConfidence = 92,
  simulationReliability = 88
}) => {
  return (
    <div className="trust-panel">
      <h3 className="trust-title">
        <Shield size={16} />
        Trust Metrics
      </h3>
      
      <TrustScore 
        label="Data Quality"
        score={dataConfidence}
        icon={Database}
        color="auto"
      />
      
      <TrustScore 
        label="AI Model Confidence"
        score={modelConfidence}
        icon={Brain}
        color="auto"
      />
      
      <TrustScore 
        label="Simulation Reliability"
        score={simulationReliability}
        icon={CheckCircle}
        color="auto"
      />
      
      <style>{`
        .trust-panel {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 16px;
          margin-bottom: 16px;
        }
        
        .trust-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          font-weight: 600;
          color: #888;
          margin: 0 0 12px 0;
          text-transform: uppercase;
        }
      `}</style>
    </div>
  );
};

export const SimpleExplanation = ({ strategy, advantage, risk }) => {
  return (
    <div className="simple-explanation">
      <div className="explanation-header">
        <h3>Strategy Recommendation</h3>
      </div>
      
      <div className="explanation-body">
        <p className="main-point">
          <strong>{strategy}</strong>
        </p>
        
        {advantage && (
          <div className="advantage">
            <CheckCircle size={16} color="#00ff64" />
            <span>{advantage}</span>
          </div>
        )}
        
        {risk && (
          <div className="risk">
            <AlertTriangle size={16} color="#ffc107" />
            <span>{risk}</span>
          </div>
        )}
      </div>
      
      <style>{`
        .simple-explanation {
          background: linear-gradient(135deg, rgba(225, 6, 0, 0.1) 0%, rgba(20, 20, 30, 0.9) 100%);
          border: 1px solid rgba(225, 6, 0, 0.3);
          border-radius: 12px;
          padding: 16px;
          margin-bottom: 16px;
        }
        
        .explanation-header {
          margin-bottom: 12px;
        }
        
        .explanation-header h3 {
          font-size: 12px;
          color: #e10600;
          text-transform: uppercase;
          margin: 0;
        }
        
        .main-point {
          font-size: 18px;
          margin: 0 0 12px 0;
          line-height: 1.4;
        }
        
        .advantage, .risk {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          margin-bottom: 8px;
          padding: 8px;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 6px;
        }
        
        .advantage {
          color: #00ff64;
        }
        
        .risk {
          color: #ffc107;
        }
      `}</style>
    </div>
  );
};

export const ConfidenceIndicator = ({ confidence, label = "Confidence" }) => {
  const getColor = (c) => {
    if (c >= 80) return "#00ff64";
    if (c >= 60) return "#ffc107";
    return "#ff6666";
  };
  
  const getLabel = (c) => {
    if (c >= 90) return "High Confidence";
    if (c >= 70) return "Good Confidence";
    if (c >= 50) return "Moderate Confidence";
    return "Low Confidence";
  };
  
  return (
    <div className="confidence-indicator">
      <div className="confidence-ring" style={{ borderColor: getColor(confidence) }}>
        <span className="confidence-value">{confidence}%</span>
      </div>
      <span className="confidence-label">{getLabel(confidence)}</span>
      
      <style>{`
        .confidence-indicator {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
        }
        
        .confidence-ring {
          width: 48px;
          height: 48px;
          border: 3px solid;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        
        .confidence-value {
          font-size: 14px;
          font-weight: 700;
        }
        
        .confidence-label {
          font-size: 14px;
          color: #888;
        }
      `}</style>
    </div>
  );
};

export default TrustPanel;

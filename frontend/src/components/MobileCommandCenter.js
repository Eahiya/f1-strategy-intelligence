/**
 * F1 Strategy Platform v4.0 - Mobile Command Center
 * Compact, mobile-optimized strategy dashboard
 */
import React, { useState, useEffect } from 'react';
import { 
  ChevronDown, 
  ChevronUp, 
  Clock, 
  MapPin, 
  Tire,
  AlertTriangle,
  TrendingUp,
  Activity,
  Play,
  History
} from 'lucide-react';
import { LineChart, Line, ResponsiveContainer, YAxis, Tooltip } from 'recharts';

const MobileCommandCenter = ({ 
  strategyResult, 
  isLoading, 
  onQuickSimulate,
  circuit = 'Monza'
}) => {
  const [expandedSection, setExpandedSection] = useState(null);
  const [quickMode, setQuickMode] = useState(true);

  // Toggle section expansion
  const toggleSection = (section) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  // Quick simulation handler
  const handleQuickSim = () => {
    if (onQuickSimulate) {
      onQuickSimulate({ circuit, strategy_type: 'auto' });
    }
  };

  // Sample data for sparkline
  const sparkData = strategyResult?.lap_times?.slice(0, 20).map((time, i) => ({
    lap: i + 1,
    time: time
  })) || [];

  if (isLoading) {
    return <CommandCenterSkeleton />;
  }

  // No results yet - show quick start
  if (!strategyResult) {
    return (
      <div className="mobile-command-center">
        <div className="quick-start-card">
          <div className="quick-start-icon">
            <Play size={32} />
          </div>
          <h2 className="quick-start-title">Quick Strategy</h2>
          <p className="quick-start-desc">
            Get optimal pit strategy in seconds
          </p>
          
          <div className="circuit-selector">
            <MapPin size={16} />
            <select 
              value={circuit} 
              onChange={() => {}}
              className="circuit-select"
            >
              <option value="Monza">Monza</option>
              <option value="Silverstone">Silverstone</option>
              <option value="Spa">Spa</option>
              <option value="Monaco">Monaco</option>
            </select>
          </div>
          
          <button 
            className="btn btn-primary btn-full-width quick-sim-btn"
            onClick={handleQuickSim}
          >
            <Play size={20} />
            Run Simulation
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mobile-command-center">
      {/* Header Summary */}
      <div className="command-header">
        <div className="circuit-badge">
          <MapPin size={14} />
          {strategyResult.circuit}
        </div>
        <div className={`strategy-badge ${strategyResult.best_strategy}`}>
          {strategyResult.best_strategy}
        </div>
      </div>

      {/* Key Metrics - Always Visible */}
      <div className="key-metrics">
        <div className="metric-card primary">
          <div className="metric-value">{strategyResult.total_time_formatted}</div>
          <div className="metric-label">Race Time</div>
        </div>
        
        <div className="metric-grid">
          <div className="metric-card">
            <div className="metric-value">
              {strategyResult.pit_laps?.length || 0}
            </div>
            <div className="metric-label">Pit Stops</div>
          </div>
          
          <div className="metric-card">
            <div className="metric-value">
              {strategyResult.tires_used?.[0]?.toUpperCase() || '-'}
            </div>
            <div className="metric-label">Start Tire</div>
          </div>
        </div>
      </div>

      {/* Expandable Sections */}
      <div className="expandable-sections">
        {/* Pit Strategy Section */}
        <div className="expandable-card">
          <button 
            className="expandable-header"
            onClick={() => toggleSection('pits')}
          >
            <div className="expandable-title">
              <Clock size={18} />
              Pit Strategy
            </div>
            {expandedSection === 'pits' ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </button>
          
          {expandedSection === 'pits' && (
            <div className="expandable-content animate-slide-up">
              {strategyResult.pit_laps?.map((lap, index) => (
                <div key={index} className="pit-item">
                  <div className="pit-lap">Lap {lap}</div>
                  <div className="pit-tire">
                    {strategyResult.tires_used?.[index + 1]?.toUpperCase() || 'TBD'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Lap Time Chart */}
        <div className="expandable-card">
          <button 
            className="expandable-header"
            onClick={() => toggleSection('chart')}
          >
            <div className="expandable-title">
              <Activity size={18} />
              Pace Analysis
            </div>
            {expandedSection === 'chart' ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </button>
          
          {expandedSection === 'chart' && sparkData.length > 0 && (
            <div className="expandable-content animate-slide-up">
              <div className="sparkline-container">
                <ResponsiveContainer width="100%" height={150}>
                  <LineChart data={sparkData}>
                    <YAxis domain={['auto', 'auto']} hide />
                    <Tooltip 
                      contentStyle={{ 
                        background: '#1a1a2e', 
                        border: '1px solid #333',
                        borderRadius: '4px',
                        fontSize: '12px'
                      }}
                      formatter={(value) => [`${typeof value === 'number' ? value.toFixed(2) : value}s`, 'Lap Time']}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="time" 
                      stroke="#e10600" 
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>

        {/* Explanation */}
        <div className="expandable-card">
          <button 
            className="expandable-header"
            onClick={() => toggleSection('explanation')}
          >
            <div className="expandable-title">
              <TrendingUp size={18} />
              Strategy Analysis
            </div>
            {expandedSection === 'explanation' ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </button>
          
          {expandedSection === 'explanation' && (
            <div className="expandable-content animate-slide-up">
              <p className="explanation-text">
                {strategyResult.explanation}
              </p>
              
              {strategyResult.strategy_comparison && (
                <div className="comparison-mini">
                  {Object.entries(strategyResult.strategy_comparison)
                    .slice(0, 3)
                    .map(([type, data]) => (
                      <div key={type} className="comparison-item">
                        <span className="comp-type">{type}</span>
                        <span className={`comp-status ${data.winner ? 'winner' : ''}`}>
                          {data.winner ? '★' : ''} {Math.floor(data.total_time / 60)}:{(typeof data.total_time === 'number' ? (data.total_time % 60).toFixed(0) : '00').padStart(2, '0')}
                        </span>
                      </div>
                    ))
                  }
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <button 
          className="btn btn-secondary"
          onClick={() => setQuickMode(!quickMode)}
        >
          <History size={18} />
          History
        </button>
        <button 
          className="btn btn-primary"
          onClick={handleQuickSim}
        >
          <Play size={18} />
          New Sim
        </button>
      </div>

      {/* Mobile-Optimized Styles */}
      <style>{`
        .mobile-command-center {
          padding: var(--space-md);
          padding-bottom: calc(var(--space-xl) + var(--nav-height));
        }

        /* Quick Start Card */
        .quick-start-card {
          background: linear-gradient(135deg, rgba(225, 6, 0, 0.1) 0%, rgba(20, 20, 30, 0.9) 100%);
          border: 1px solid rgba(225, 6, 0, 0.3);
          border-radius: 16px;
          padding: var(--space-xl);
          text-align: center;
          margin-bottom: var(--space-xl);
        }

        .quick-start-icon {
          width: 64px;
          height: 64px;
          background: linear-gradient(135deg, #e10600 0%, #ff3300 100%);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto var(--space-lg);
          color: white;
        }

        .quick-start-title {
          font-size: var(--text-xl);
          font-weight: 700;
          margin: 0 0 var(--space-sm) 0;
        }

        .quick-start-desc {
          color: #888;
          font-size: var(--text-base);
          margin: 0 0 var(--space-xl) 0;
        }

        .circuit-selector {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-sm);
          background: rgba(255, 255, 255, 0.05);
          padding: var(--space-md);
          border-radius: 8px;
          margin-bottom: var(--space-lg);
          color: #aaa;
        }

        .circuit-select {
          background: transparent;
          border: none;
          color: #fff;
          font-size: var(--text-lg);
          font-weight: 600;
          cursor: pointer;
        }

        .quick-sim-btn {
          font-size: var(--text-lg);
          min-height: 56px;
        }

        /* Command Header */
        .command-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--space-md);
        }

        .circuit-badge {
          display: flex;
          align-items: center;
          gap: var(--space-xs);
          background: rgba(255, 255, 255, 0.05);
          padding: var(--space-xs) var(--space-md);
          border-radius: 20px;
          font-size: var(--text-sm);
          color: #aaa;
        }

        .strategy-badge {
          padding: var(--space-xs) var(--space-md);
          border-radius: 20px;
          font-size: var(--text-sm);
          font-weight: 600;
          text-transform: uppercase;
        }

        .strategy-badge._2_stop {
          background: rgba(225, 6, 0, 0.2);
          color: #ff6666;
        }

        .strategy-badge._1_stop {
          background: rgba(0, 255, 100, 0.2);
          color: #00ff64;
        }

        .strategy-badge._3_stop {
          background: rgba(255, 193, 7, 0.2);
          color: #ffc107;
        }

        /* Key Metrics */
        .key-metrics {
          margin-bottom: var(--space-lg);
        }

        .metric-card {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: var(--space-lg);
          text-align: center;
        }

        .metric-card.primary {
          background: linear-gradient(135deg, rgba(225, 6, 0, 0.1) 0%, rgba(20, 20, 30, 0.9) 100%);
          border-color: rgba(225, 6, 0, 0.3);
          margin-bottom: var(--space-md);
        }

        .metric-value {
          font-size: 28px;
          font-weight: 700;
          color: #fff;
          margin-bottom: var(--space-xs);
        }

        .metric-card.primary .metric-value {
          font-size: 36px;
          background: linear-gradient(135deg, #fff 0%, #e10600 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .metric-label {
          font-size: var(--text-sm);
          color: #888;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .metric-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: var(--space-md);
        }

        /* Expandable Sections */
        .expandable-card {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          margin-bottom: var(--space-md);
          overflow: hidden;
        }

        .expandable-header {
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: var(--space-md) var(--space-lg);
          background: transparent;
          border: none;
          color: #fff;
          font-size: var(--text-base);
          cursor: pointer;
          min-height: var(--touch-comfortable);
        }

        .expandable-title {
          display: flex;
          align-items: center;
          gap: var(--space-md);
          font-weight: 600;
        }

        .expandable-content {
          padding: 0 var(--space-lg) var(--space-lg);
          border-top: 1px solid rgba(255, 255, 255, 0.05);
        }

        .pit-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--space-md) 0;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .pit-item:last-child {
          border-bottom: none;
        }

        .pit-lap {
          font-weight: 600;
        }

        .pit-tire {
          color: #888;
          font-size: var(--text-sm);
        }

        /* Sparkline */
        .sparkline-container {
          margin-top: var(--space-md);
        }

        /* Explanation */
        .explanation-text {
          font-size: var(--text-sm);
          line-height: 1.6;
          color: #aaa;
          margin: 0 0 var(--space-lg) 0;
        }

        .comparison-mini {
          display: flex;
          flex-direction: column;
          gap: var(--space-sm);
        }

        .comparison-item {
          display: flex;
          justify-content: space-between;
          padding: var(--space-sm) 0;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .comp-type {
          text-transform: uppercase;
          font-size: var(--text-xs);
          color: #888;
        }

        .comp-status {
          font-family: monospace;
        }

        .comp-status.winner {
          color: #00ff64;
        }

        /* Quick Actions */
        .quick-actions {
          display: flex;
          gap: var(--space-md);
          position: fixed;
          bottom: calc(var(--nav-height) + var(--space-md));
          left: var(--space-md);
          right: var(--space-md);
          z-index: 50;
        }

        .quick-actions .btn {
          flex: 1;
        }

        .btn-secondary {
          background: rgba(255, 255, 255, 0.1);
          color: #fff;
        }

        /* Skeleton Loading */
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}</style>
    </div>
  );
};

// Loading skeleton
const CommandCenterSkeleton = () => (
  <div className="mobile-command-center">
    <div className="skeleton-card" style={{ 
      height: '200px', 
      background: 'linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.03) 75%)',
      backgroundSize: '200% 100%',
      animation: 'shimmer 1.5s infinite'
    }} />
    <div className="skeleton-card" style={{ 
      height: '100px', 
      marginTop: '16px',
      background: 'linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.03) 75%)',
      backgroundSize: '200% 100%',
      animation: 'shimmer 1.5s infinite'
    }} />
  </div>
);

export default MobileCommandCenter;

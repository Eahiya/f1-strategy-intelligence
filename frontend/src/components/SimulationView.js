/**
 * F1 Strategy Platform v4.0 - Simulation View
 * Responsive simulation interface
 */
import React, { useState, useEffect } from 'react';
import { Play, ChevronDown, ChevronUp } from 'lucide-react';

const SimulationView = ({ deviceType, api }) => {
  const [circuit, setCircuit] = useState('Monza');
  const [strategyType, setStrategyType] = useState('auto');
  const [weather, setWeather] = useState('dry');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [circuits, setCircuits] = useState([]);
  const [advancedOpen, setAdvancedOpen] = useState(false);

  useEffect(() => {
    fetchCircuits();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchCircuits = async () => {
    try {
      const response = await api.get('/circuits');
      setCircuits(response.data.circuits);
    } catch (err) {
      console.error('Failed to load circuits:', err);
    }
  };

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const response = await api.post('/simulate', {
        circuit,
        strategy_type: strategyType,
        weather,
        tire_compound: 'soft'
      });
      setResult(response.data);
    } catch (err) {
      console.error('Simulation failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="simulation-view">
      <h1 className="page-title">Strategy Simulation</h1>
      
      <div className={`simulation-form ${deviceType}`}>
        {/* Quick Mode (Mobile-First) */}
        <div className="quick-mode">
          <div className="form-group">
            <label className="form-label">Circuit</label>
            <select 
              className="form-select"
              value={circuit}
              onChange={(e) => setCircuit(e.target.value)}
            >
              {circuits.map(c => (
                <option key={c.name} value={c.name}>{c.name}</option>
              ))}
            </select>
          </div>

          <button 
            className="btn btn-primary btn-full-width"
            onClick={handleSimulate}
            disabled={loading}
          >
            <Play size={20} />
            {loading ? 'Simulating...' : 'Run Simulation'}
          </button>
        </div>

        {/* Advanced Options (Collapsible on Mobile) */}
        {deviceType === 'mobile' && (
          <button 
            className="advanced-toggle"
            onClick={() => setAdvancedOpen(!advancedOpen)}
          >
            Advanced Options
            {advancedOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </button>
        )}

        {(advancedOpen || deviceType !== 'mobile') && (
          <div className="advanced-options">
            <div className="form-group">
              <label className="form-label">Strategy Type</label>
              <select 
                className="form-select"
                value={strategyType}
                onChange={(e) => setStrategyType(e.target.value)}
              >
                <option value="auto">Auto (Optimal)</option>
                <option value="1_stop">1 Stop</option>
                <option value="2_stop">2 Stop</option>
                <option value="3_stop">3 Stop</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Weather</label>
              <select 
                className="form-select"
                value={weather}
                onChange={(e) => setWeather(e.target.value)}
              >
                <option value="dry">Dry</option>
                <option value="wet">Wet</option>
                <option value="mixed">Mixed</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <div className="results-card animate-slide-up">
          <h2 className="results-title">Results: {result.best_strategy}</h2>
          <div className="results-metrics">
            <div className="result-metric">
              <span className="metric-value">{result.total_time_formatted}</span>
              <span className="metric-label">Total Time</span>
            </div>
            <div className="result-metric">
              <span className="metric-value">{result.pit_laps?.length || 0}</span>
              <span className="metric-label">Pit Stops</span>
            </div>
          </div>
          <p className="results-explanation">{result.explanation}</p>
        </div>
      )}

      <style>{`
        .simulation-view {
          padding-bottom: 80px;
        }
        
        .page-title {
          font-size: 24px;
          font-weight: 700;
          margin: 0 0 20px 0;
        }
        
        .simulation-form {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 16px;
          padding: 20px;
          margin-bottom: 20px;
        }
        
        .quick-mode {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        
        .advanced-toggle {
          width: 100%;
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: none;
          border: none;
          color: #888;
          padding: 16px 0;
          margin-top: 8px;
          border-top: 1px solid rgba(255, 255, 255, 0.1);
          font-size: 14px;
          cursor: pointer;
        }
        
        .advanced-options {
          padding-top: 16px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        
        .results-card {
          background: rgba(225, 6, 0, 0.05);
          border: 1px solid rgba(225, 6, 0, 0.3);
          border-radius: 16px;
          padding: 20px;
        }
        
        .results-title {
          font-size: 18px;
          font-weight: 600;
          margin: 0 0 16px 0;
          color: #e10600;
        }
        
        .results-metrics {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
          margin-bottom: 16px;
        }
        
        .result-metric {
          text-align: center;
          background: rgba(255, 255, 255, 0.05);
          padding: 16px;
          border-radius: 8px;
        }
        
        .results-explanation {
          font-size: 14px;
          line-height: 1.6;
          color: #aaa;
          margin: 0;
        }
        
        @media (min-width: 768px) {
          .simulation-form {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
          }
          
          .quick-mode {
            grid-column: span 2;
          }
        }
      `}</style>
    </div>
  );
};

export default SimulationView;

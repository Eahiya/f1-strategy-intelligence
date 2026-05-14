import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Context Providers (in order of dependency)
import { SettingsProvider } from './context/SettingsContext';
import { NotificationProvider } from './context/NotificationContext';
import { AuthProvider } from './context/AuthContext';
import { RaceProvider } from './context/RaceContext';
import { SyntheticBannerProvider } from './contexts/SyntheticBannerContext';
import SyntheticBanner from './notifications/SyntheticBanner';

// Components
import ErrorBoundary from './components/ErrorBoundary';
import ProtectedRoute from './components/auth/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import { NavigationSidebar } from './components/f1';
import DashboardContent from './pages/Dashboard';
import { LiveRaceWeekend, HeadToHeadComparison, WeatherForecastPanel, MultiCarSimulation, OpponentAnalysisPanel, HistoricalStrategyBrowser } from './components/f1';

const TAB_COMPONENTS = {
  dashboard: DashboardContent,
  live: LiveRaceWeekend,
  headtohead: HeadToHeadComparison,
  weather: WeatherForecastPanel,
  multicar: MultiCarSimulation,
  opponent: OpponentAnalysisPanel,
  history: HistoricalStrategyBrowser,
};

const DashboardWithNav = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const ActiveComponent = TAB_COMPONENTS[activeTab] || DashboardContent;
  const isDashboard = activeTab === 'dashboard';

  return (
    <div className="min-h-screen bg-[#050505] text-white">
      <div className="fixed inset-0 bg-[linear-gradient(rgba(255,255,255,0.01)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.01)_1px,transparent_1px)] bg-[size:80px_80px] pointer-events-none" />
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_50%_0%,rgba(225,6,0,0.06)_0%,transparent_60%)] pointer-events-none" />
      <NavigationSidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="pl-[56px] md:pl-[200px] transition-all duration-300">
        <div className="p-4 md:p-6 max-w-[1920px] mx-auto">
          {isDashboard ? (
            <DashboardContent />
          ) : (
            <div className="f1-card p-5">
              <ActiveComponent />
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

const App = () => {
  return (
    <ErrorBoundary>
      <SettingsProvider>
        <NotificationProvider>
          <AuthProvider>
            <RaceProvider>
              <SyntheticBannerProvider>
                <Router>
                <Routes>
                  <Route path="/login" element={<LoginPage />} />
                  <Route
                    path="/"
                    element={
                      <ProtectedRoute>
                        <DashboardWithNav />
                      </ProtectedRoute>
                    }
                  />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Router>
              <SyntheticBanner />
            </SyntheticBannerProvider>
            </RaceProvider>
          </AuthProvider>
        </NotificationProvider>
      </SettingsProvider>
    </ErrorBoundary>
  );
};

export default App;

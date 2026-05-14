/**
 * F1 Strategy Platform v4.0 - Skeleton Loader
 * Skeleton screens for better perceived performance
 */
import React from 'react';

export const SkeletonCard = ({ height = 120 }) => (
  <div 
    className="skeleton skeleton-card"
    style={{ height }}
  />
);

export const SkeletonText = ({ lines = 3 }) => (
  <div className="skeleton-text">
    {Array.from({ length: lines }).map((_, i) => (
      <div 
        key={i} 
        className="skeleton skeleton-line"
        style={{ width: `${Math.random() * 40 + 60}%` }}
      />
    ))}
  </div>
);

export const SkeletonChart = () => (
  <div className="skeleton skeleton-chart">
    <svg viewBox="0 0 400 200" className="skeleton-chart-svg">
      <path
        d="M0,150 Q100,100 200,120 T400,80"
        fill="none"
        stroke="rgba(255,255,255,0.1)"
        strokeWidth="2"
      />
    </svg>
  </div>
);

export const SkeletonMetric = () => (
  <div className="skeleton-metric">
    <div className="skeleton skeleton-value" />
    <div className="skeleton skeleton-label" />
  </div>
);

export const DashboardSkeleton = () => (
  <div className="dashboard-skeleton">
    <div className="skeleton skeleton-title" />
    <div className="dashboard-grid-skeleton">
      <SkeletonCard height={150} />
      <SkeletonCard height={150} />
      <SkeletonCard height={200} />
      <SkeletonChart />
    </div>
    <style>{`
      .dashboard-skeleton {
        padding: 16px;
      }
      
      .skeleton-title {
        height: 28px;
        width: 200px;
        border-radius: 4px;
        margin-bottom: 20px;
      }
      
      .dashboard-grid-skeleton {
        display: grid;
        gap: 16px;
        grid-template-columns: 1fr;
      }
      
      @media (min-width: 768px) {
        .dashboard-grid-skeleton {
          grid-template-columns: repeat(2, 1fr);
        }
      }
      
      @media (min-width: 1024px) {
        .dashboard-grid-skeleton {
          grid-template-columns: repeat(3, 1fr);
        }
      }
    `}</style>
  </div>
);

// Main skeleton with shimmer animation styles
const SkeletonLoader = () => (
  <>
    <style>{`
      .skeleton {
        background: linear-gradient(
          90deg,
          rgba(255, 255, 255, 0.03) 25%,
          rgba(255, 255, 255, 0.08) 50%,
          rgba(255, 255, 255, 0.03) 75%
        );
        background-size: 200% 100%;
        border-radius: 8px;
        animation: shimmer 1.5s infinite;
      }
      
      @keyframes shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
      }
      
      .skeleton-card {
        border-radius: 12px;
      }
      
      .skeleton-text {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      
      .skeleton-line {
        height: 16px;
        border-radius: 4px;
      }
      
      .skeleton-chart {
        height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      
      .skeleton-chart-svg {
        width: 100%;
        height: 100%;
      }
      
      .skeleton-metric {
        padding: 20px;
        text-align: center;
      }
      
      .skeleton-value {
        height: 36px;
        width: 80px;
        margin: 0 auto 8px;
        border-radius: 4px;
      }
      
      .skeleton-label {
        height: 14px;
        width: 60px;
        margin: 0 auto;
        border-radius: 4px;
      }
    `}</style>
  </>
);

export default SkeletonLoader;

"""
F1 Strategy Platform v5.0 - Analytics & Usage Tracking
Tracks user behavior, feature usage, and system performance.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict
import logging
import statistics
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON
from sqlalchemy.orm import Session

from app.auth.models import Base

logger = logging.getLogger(__name__)


class AnalyticsEvent(Base):
    """Database model for analytics events."""
    __tablename__ = "analytics_events"
    
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    session_id = Column(String(100), nullable=True)
    
    # Event data
    feature = Column(String(50), nullable=True)  # e.g., 'simulation', 'elite_rl'
    action = Column(String(50), nullable=True)     # e.g., 'run', 'view', 'export'
    circuit = Column(String(50), nullable=True)
    
    # Metadata
    properties = Column(JSON, default=dict)      # Additional event properties
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Performance
    duration_ms = Column(Float, nullable=True)
    success = Column(String, default="true")
    error_message = Column(Text, nullable=True)
    
    # Client info
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)


class AnalyticsService:
    """
    Service for tracking and analyzing user behavior.
    
    Features:
    - Event tracking
    - Feature usage analytics
    - User behavior insights
    - Performance metrics
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def track_event(
        self,
        event_type: str,
        user_id: int = None,
        feature: str = None,
        action: str = None,
        properties: Dict = None,
        duration_ms: float = None,
        success: bool = True,
        error_message: str = None,
        session_id: str = None,
        user_agent: str = None,
        ip_address: str = None
    ) -> AnalyticsEvent:
        """
        Track an analytics event.
        
        Args:
            event_type: Type of event (e.g., 'feature_used', 'simulation_run')
            user_id: User ID (optional for anonymous tracking)
            feature: Feature name
            action: Action performed
            properties: Additional properties
            duration_ms: Event duration in milliseconds
            success: Whether the action succeeded
            error_message: Error message if failed
            session_id: Session identifier
            user_agent: Client user agent
            ip_address: Client IP
        
        Returns:
            AnalyticsEvent object
        """
        event = AnalyticsEvent(
            event_type=event_type,
            user_id=user_id,
            feature=feature,
            action=action,
            properties=properties or {},
            duration_ms=duration_ms,
            success="true" if success else "false",
            error_message=error_message,
            session_id=session_id,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        self.db.add(event)
        self.db.commit()
        
        return event
    
    def track_simulation(
        self,
        user_id: int,
        circuit: str,
        strategy_type: str,
        duration_ms: float,
        success: bool,
        simulation_type: str = "basic",
        properties: Dict = None
    ):
        """Track simulation event."""
        return self.track_event(
            event_type="simulation_run",
            user_id=user_id,
            feature="simulation",
            action="run",
            circuit=circuit,
            properties={
                "strategy_type": strategy_type,
                "simulation_type": simulation_type,
                **(properties or {})
            },
            duration_ms=duration_ms,
            success=success
        )
    
    def track_feature_usage(
        self,
        user_id: int,
        feature: str,
        action: str,
        properties: Dict = None
    ):
        """Track feature usage."""
        return self.track_event(
            event_type="feature_used",
            user_id=user_id,
            feature=feature,
            action=action,
            properties=properties
        )
    
    def track_error(
        self,
        user_id: int,
        feature: str,
        error_type: str,
        error_message: str,
        properties: Dict = None
    ):
        """Track error events."""
        return self.track_event(
            event_type="error",
            user_id=user_id,
            feature=feature,
            action="error",
            properties={
                "error_type": error_type,
                **(properties or {})
            },
            success=False,
            error_message=error_message
        )
    
    def get_feature_usage_stats(
        self,
        days: int = 30,
        feature: str = None
    ) -> Dict[str, Any]:
        """
        Get feature usage statistics.
        
        Args:
            days: Number of days to analyze
            feature: Optional feature filter
        
        Returns:
            Usage statistics dict
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(AnalyticsEvent).filter(
            AnalyticsEvent.timestamp >= start_date,
            AnalyticsEvent.event_type == "feature_used"
        )
        
        if feature:
            query = query.filter(AnalyticsEvent.feature == feature)
        
        events = query.all()
        
        if not events:
            return {
                "period_days": days,
                "total_events": 0,
                "features": {}
            }
        
        # Aggregate by feature
        feature_stats = defaultdict(lambda: {"count": 0, "actions": defaultdict(int)})
        
        for event in events:
            feature_stats[event.feature]["count"] += 1
            feature_stats[event.feature]["actions"][event.action] += 1
        
        # Calculate percentages
        total = len(events)
        for feat in feature_stats:
            feature_stats[feat]["percentage"] = (feature_stats[feat]["count"] / total) * 100
        
        return {
            "period_days": days,
            "total_events": total,
            "unique_users": len(set(e.user_id for e in events if e.user_id)),
            "features": dict(feature_stats),
            "top_feature": max(feature_stats.items(), key=lambda x: x[1]["count"])[0] if feature_stats else None
        }
    
    def get_simulation_stats(self, days: int = 30) -> Dict:
        """Get simulation statistics."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        events = self.db.query(AnalyticsEvent).filter(
            AnalyticsEvent.timestamp >= start_date,
            AnalyticsEvent.event_type == "simulation_run"
        ).all()
        
        if not events:
            return {
                "period_days": days,
                "total_simulations": 0,
                "success_rate": 0,
                "circuits": {},
                "strategy_types": {}
            }
        
        # Aggregate statistics
        total = len(events)
        successful = sum(1 for e in events if e.success == "true")
        
        circuits = defaultdict(int)
        strategy_types = defaultdict(int)
        durations = []
        
        for event in events:
            if event.circuit:
                circuits[event.circuit] += 1
            
            if event.properties and "strategy_type" in event.properties:
                strategy_types[event.properties["strategy_type"]] += 1
            
            if event.duration_ms:
                durations.append(event.duration_ms)
        
        return {
            "period_days": days,
            "total_simulations": total,
            "successful_simulations": successful,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "circuits": dict(circuits),
            "strategy_types": dict(strategy_types),
            "avg_duration_ms": statistics.mean(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "users_count": len(set(e.user_id for e in events if e.user_id))
        }
    
    def get_user_activity(self, user_id: int, days: int = 30) -> Dict:
        """Get activity stats for a specific user."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        events = self.db.query(AnalyticsEvent).filter(
            AnalyticsEvent.timestamp >= start_date,
            AnalyticsEvent.user_id == user_id
        ).all()
        
        if not events:
            return {
                "user_id": user_id,
                "period_days": days,
                "total_events": 0,
                "most_used_feature": None
            }
        
        # Feature usage
        feature_counts = defaultdict(int)
        for event in events:
            if event.feature:
                feature_counts[event.feature] += 1
        
        # Daily activity
        daily_counts = defaultdict(int)
        for event in events:
            day = event.timestamp.date().isoformat()
            daily_counts[day] += 1
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_events": len(events),
            "feature_usage": dict(feature_counts),
            "most_used_feature": max(feature_counts.items(), key=lambda x: x[1])[0] if feature_counts else None,
            "daily_activity": dict(daily_counts),
            "last_active": max(e.timestamp for e in events).isoformat()
        }
    
    def get_performance_metrics(self, days: int = 7) -> Dict:
        """Get system performance metrics."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        events = self.db.query(AnalyticsEvent).filter(
            AnalyticsEvent.timestamp >= start_date,
            AnalyticsEvent.duration_ms is not None
        ).all()
        
        if not events:
            return {
                "period_days": days,
                "metrics": {}
            }
        
        # Group by feature
        feature_durations = defaultdict(list)
        for event in events:
            if event.feature:
                feature_durations[event.feature].append(event.duration_ms)
        
        metrics = {}
        for feature, durations in feature_durations.items():
            if durations:
                metrics[feature] = {
                    "avg_ms": statistics.mean(durations),
                    "median_ms": statistics.median(durations),
                    "p95_ms": self._percentile(durations, 95),
                    "p99_ms": self._percentile(durations, 99),
                    "max_ms": max(durations),
                    "min_ms": min(durations)
                }
        
        return {
            "period_days": days,
            "metrics": metrics
        }
    
    def get_error_analytics(self, days: int = 7) -> Dict:
        """Get error analytics."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        errors = self.db.query(AnalyticsEvent).filter(
            AnalyticsEvent.timestamp >= start_date,
            AnalyticsEvent.success == "false"
        ).all()
        
        if not errors:
            return {
                "period_days": days,
                "total_errors": 0,
                "error_types": {},
                "affected_features": {}
            }
        
        # Aggregate
        error_types = defaultdict(int)
        affected_features = defaultdict(int)
        
        for error in errors:
            if error.properties and "error_type" in error.properties:
                error_types[error.properties["error_type"]] += 1
            
            if error.feature:
                affected_features[error.feature] += 1
        
        return {
            "period_days": days,
            "total_errors": len(errors),
            "unique_users_affected": len(set(e.user_id for e in errors if e.user_id)),
            "error_types": dict(error_types),
            "affected_features": dict(affected_features),
            "most_problematic_feature": max(affected_features.items(), key=lambda x: x[1])[0] if affected_features else None
        }
    
    def get_dashboard_summary(self) -> Dict:
        """Get high-level dashboard summary."""
        today = datetime.utcnow().date()
        
        # Today's stats
        today_start = datetime.combine(today, datetime.min.time())
        
        today_events = self.db.query(AnalyticsEvent).filter(
            AnalyticsEvent.timestamp >= today_start
        ).count()
        
        today_simulations = self.db.query(AnalyticsEvent).filter(
            AnalyticsEvent.timestamp >= today_start,
            AnalyticsEvent.event_type == "simulation_run"
        ).count()
        
        # Last 7 days trend
        week_stats = self.get_simulation_stats(days=7)
        
        # Top features this week
        feature_stats = self.get_feature_usage_stats(days=7)
        
        # Error rate
        error_stats = self.get_error_analytics(days=7)
        total_week_events = self.db.query(AnalyticsEvent).filter(
            AnalyticsEvent.timestamp >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        error_rate = (error_stats["total_errors"] / total_week_events * 100) if total_week_events > 0 else 0
        
        return {
            "today": {
                "total_events": today_events,
                "simulations": today_simulations
            },
            "week": {
                "total_simulations": week_stats["total_simulations"],
                "unique_users": week_stats["users_count"],
                "success_rate": week_stats["success_rate"],
                "error_rate": error_rate,
                "top_feature": feature_stats.get("top_feature"),
                "most_used_circuit": max(week_stats["circuits"].items(), key=lambda x: x[1])[0] if week_stats["circuits"] else None
            }
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile."""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * (percentile / 100))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def export_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "json"
    ) -> Dict:
        """Export analytics data for a date range."""
        events = self.db.query(AnalyticsEvent).filter(
            AnalyticsEvent.timestamp >= start_date,
            AnalyticsEvent.timestamp <= end_date
        ).all()
        
        data = [{
            "id": e.id,
            "event_type": e.event_type,
            "user_id": e.user_id,
            "feature": e.feature,
            "action": e.action,
            "circuit": e.circuit,
            "properties": e.properties,
            "timestamp": e.timestamp.isoformat(),
            "duration_ms": e.duration_ms,
            "success": e.success == "true"
        } for e in events]
        
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_events": len(data),
            "data": data
        }


# Import for statistics

if __name__ == "__main__":
    print("Analytics Service")
    print("=" * 60)
    print("This module provides:")
    print("  ✓ Event tracking")
    print("  ✓ Feature usage analytics")
    print("  ✓ User behavior insights")
    print("  ✓ Performance metrics")
    print("  ✓ Error analytics")
    print("  ✓ Dashboard summaries")
    print("\nReady for integration with FastAPI endpoints.")

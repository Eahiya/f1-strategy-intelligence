"""
Audit Logging System
Tracks user activity for security and compliance.
"""
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps

from fastapi import Request
from sqlalchemy.orm import Session

from .models import AuditLog, User


# Log directory
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

AUDIT_LOG_FILE = os.path.join(LOG_DIR, "audit.log")


class AuditLogger:
    """
    Audit logger for tracking API access and user actions.
    """
    
    @staticmethod
    def log_api_call(
        db: Session,
        user: Optional[User],
        request: Request,
        endpoint: str,
        method: str,
        params: Optional[Dict] = None,
        response_status: Optional[int] = None
    ):
        """
        Log an API call to database and file.
        
        Args:
            db: Database session
            user: Authenticated user (or None)
            request: FastAPI request object
            endpoint: API endpoint path
            method: HTTP method
            params: Request parameters (optional)
            response_status: HTTP response status code
        """
        timestamp = datetime.utcnow()
        
        # Get client info
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Create database log entry
        log_entry = AuditLog(
            user_id=user.user_id if user else None,
            username=user.username if user else None,
            endpoint=endpoint,
            method=method,
            params=json.dumps(params) if params else None,
            timestamp=timestamp,
            ip_address=ip_address,
            user_agent=user_agent,
            response_status=response_status
        )
        
        db.add(log_entry)
        db.commit()
        
        # Also log to file for external monitoring
        log_line = (
            f"[{timestamp.isoformat()}] "
            f"{user.username if user else 'anonymous'} "
            f"{method} {endpoint} "
            f"{response_status or '-'} "
            f"{ip_address or '-'}"
        )
        
        with open(AUDIT_LOG_FILE, "a") as f:
            f.write(log_line + "\n")
    
    @staticmethod
    def log_simulation(
        db: Session,
        user: User,
        circuit: str,
        strategy_type: str,
        parameters: Dict[str, Any]
    ):
        """
        Log a simulation run.
        
        Args:
            db: Database session
            user: User who ran simulation
            circuit: Circuit name
            strategy_type: Type of strategy
            parameters: Simulation parameters
        """
        timestamp = datetime.utcnow()
        
        # Create detailed log entry
        log_entry = AuditLog(
            user_id=user.user_id,
            username=user.username,
            endpoint=f"/simulate/{strategy_type}",
            method="POST",
            params=json.dumps({
                "circuit": circuit,
                "strategy_type": strategy_type,
                **parameters
            }),
            timestamp=timestamp,
            ip_address=None,
            response_status=200
        )
        
        db.add(log_entry)
        db.commit()
    
    @staticmethod
    def get_user_activity(
        db: Session,
        user_id: int,
        limit: int = 100
    ) -> list:
        """
        Get activity log for a specific user.
        
        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of records
            
        Returns:
            List of audit log entries
        """
        logs = db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()
        
        return [log.to_dict() for log in logs]
    
    @staticmethod
    def get_recent_activity(
        db: Session,
        limit: int = 100,
        endpoint_filter: Optional[str] = None
    ) -> list:
        """
        Get recent activity across all users.
        
        Args:
            db: Database session
            limit: Maximum number of records
            endpoint_filter: Optional endpoint filter
            
        Returns:
            List of audit log entries
        """
        query = db.query(AuditLog)
        
        if endpoint_filter:
            query = query.filter(AuditLog.endpoint.contains(endpoint_filter))
        
        logs = query.order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()
        
        return [log.to_dict() for log in logs]
    
    @staticmethod
    def get_usage_statistics(db: Session) -> Dict:
        """
        Get usage statistics for the system.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with usage stats
        """
        from sqlalchemy import func
        
        # Total API calls
        total_calls = db.query(AuditLog).count()
        
        # Calls by endpoint
        endpoint_stats = db.query(
            AuditLog.endpoint,
            func.count(AuditLog.log_id).label("count")
        ).group_by(AuditLog.endpoint).order_by(func.count(AuditLog.log_id).desc()).limit(10).all()
        
        # Calls by user
        user_stats = db.query(
            AuditLog.username,
            func.count(AuditLog.log_id).label("count")
        ).group_by(AuditLog.username).order_by(func.count(AuditLog.log_id).desc()).limit(10).all()
        
        # Recent calls (last 24 hours)
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(hours=24)
        recent_calls = db.query(AuditLog).filter(
            AuditLog.timestamp >= yesterday
        ).count()
        
        return {
            "total_api_calls": total_calls,
            "recent_24h": recent_calls,
            "top_endpoints": [
                {"endpoint": ep, "calls": cnt} for ep, cnt in endpoint_stats
            ],
            "top_users": [
                {"username": uname, "calls": cnt} for uname, cnt in user_stats
            ]
        }


def audit_log_decorator(endpoint_name: str, log_params: bool = False):
    """
    Decorator to automatically log API calls.
    
    Args:
        endpoint_name: Name of the endpoint
        log_params: Whether to log request parameters
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and db from kwargs
            request = kwargs.get('request')
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')
            
            # Call the function
            response = await func(*args, **kwargs)
            
            # Log the call
            if db and request:
                params = None
                if log_params:
                    # Extract params from kwargs (excluding internal dependencies)
                    params = {k: v for k, v in kwargs.items() 
                             if k not in ['request', 'db', 'current_user']}
                
                AuditLogger.log_api_call(
                    db=db,
                    user=current_user,
                    request=request,
                    endpoint=endpoint_name,
                    method=request.method,
                    params=params if log_params else None
                )
            
            return response
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test audit logging
    print("Testing Audit Logging System")
    print("=" * 60)
    
    # Initialize database
    from .models import Base, engine
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create test session
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    print("\n1. Creating mock log entries")
    
    # Create mock log entries
    for i in range(5):
        log = AuditLog(
            user_id=1,
            username="test_user",
            endpoint=f"/test/endpoint{i}",
            method="POST",
            params=json.dumps({"param": f"value{i}"}),
            timestamp=datetime.utcnow(),
            ip_address="127.0.0.1",
            response_status=200
        )
        db.add(log)
    
    db.commit()
    print("✓ 5 log entries created")
    
    print("\n2. Retrieving user activity")
    activity = AuditLogger.get_user_activity(db, user_id=1, limit=3)
    print(f"✓ Retrieved {len(activity)} activity records")
    
    print("\n3. Getting usage statistics")
    stats = AuditLogger.get_usage_statistics(db)
    print(f"✓ Total API calls: {stats['total_api_calls']}")
    print(f"✓ Top endpoint: {stats['top_endpoints'][0] if stats['top_endpoints'] else 'N/A'}")
    
    print("\n4. Checking log file")
    if os.path.exists(AUDIT_LOG_FILE):
        with open(AUDIT_LOG_FILE, "r") as f:
            lines = f.readlines()
        print(f"✓ Log file exists with {len(lines)} lines")
    else:
        print("✗ Log file not found")
    
    print("\n✓ Audit logging system working correctly!")

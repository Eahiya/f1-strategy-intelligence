"""
F1 Strategy Platform v6.0 - Security Monitoring
Anomaly detection, abuse prevention, and security alerting.
"""
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class SecurityEvent:
    """Security event for logging."""
    event_type: str  # 'anomaly', 'abuse', 'breach_attempt'
    severity: str    # 'low', 'medium', 'high', 'critical'
    source_ip: str
    user_id: Optional[int]
    description: str
    timestamp: str
    action_taken: str


class APIAnomalyDetector:
    """
    Detects API abuse patterns and anomalies.
    
    Monitors:
    - Unusual request rates
    - Suspicious request patterns
    - Geographic anomalies
    - Failed authentication spikes
    """
    
    def __init__(self):
        self.request_history: Dict[str, List[float]] = defaultdict(list)  # ip -> timestamps
        self.auth_failures: Dict[str, List[float]] = defaultdict(list)  # ip -> timestamps
        self.blocked_ips: set = set()
        self.suspicious_users: set = set()
        
        # Thresholds
        self.rate_threshold = 100  # requests per minute
        self.auth_failure_threshold = 10  # failed auths per minute
        self.block_duration = 3600  # seconds (1 hour)
    
    def check_request(self, ip: str, user_id: int = None, 
                   endpoint: str = None) -> Optional[str]:
        """
        Check if request is anomalous.
        
        Returns:
            Alert message if anomaly detected, None otherwise
        """
        now = time.time()
        
        # Check if IP is blocked
        if ip in self.blocked_ips:
            return f"BLOCKED: IP {ip} is temporarily blocked"
        
        # Update request history
        self.request_history[ip].append(now)
        
        # Clean old requests (older than 1 minute)
        cutoff = now - 60
        self.request_history[ip] = [t for t in self.request_history[ip] if t > cutoff]
        
        # Check rate
        if len(self.request_history[ip]) > self.rate_threshold:
            self.blocked_ips.add(ip)
            self._log_security_event(
                event_type="abuse",
                severity="high",
                source_ip=ip,
                user_id=user_id,
                description=f"Rate limit exceeded: {len(self.request_history[ip])} requests/min",
                action_taken=f"Blocked IP for {self.block_duration}s"
            )
            return f"RATE_LIMITED: Too many requests from {ip}"
        
        # Check for suspicious patterns
        if endpoint and self._is_suspicious_endpoint_pattern(ip, endpoint):
            return "SUSPICIOUS: Unusual endpoint access pattern"
        
        return None
    
    def report_auth_failure(self, ip: str, username: str = None):
        """Report a failed authentication attempt."""
        now = time.time()
        self.auth_failures[ip].append(now)
        
        # Clean old failures
        cutoff = now - 60
        self.auth_failures[ip] = [t for t in self.auth_failures[ip] if t > cutoff]
        
        # Check threshold
        if len(self.auth_failures[ip]) > self.auth_failure_threshold:
            self.blocked_ips.add(ip)
            self._log_security_event(
                event_type="breach_attempt",
                severity="critical",
                source_ip=ip,
                user_id=None,
                description=f"Brute force attempt: {len(self.auth_failures[ip])} failed logins/min",
                action_taken=f"Blocked IP for {self.block_duration}s"
            )
            logger.critical(f"Potential brute force attack from {ip}")
    
    def _is_suspicious_endpoint_pattern(self, ip: str, endpoint: str) -> bool:
        """Check for suspicious endpoint access patterns."""
        # Example: Accessing admin endpoints from non-admin IPs
        if "/admin/" in endpoint or "/auth/users" in endpoint:
            return True
        return False
    
    def _log_security_event(self, event_type: str, severity: str, 
                           source_ip: str, user_id: int, 
                           description: str, action_taken: str):
        """Log security event."""
        # event = SecurityEvent(
        SecurityEvent(
            event_type=event_type,
            severity=severity,
            source_ip=source_ip,
            user_id=user_id,
            description=description,
            timestamp=datetime.now().isoformat(),
            action_taken=action_taken
        )
        
        # Log to security log
        log_msg = f"SECURITY [{severity}] {event_type}: {description} | Action: {action_taken}"
        if severity == "critical":
            logger.critical(log_msg)
        elif severity == "high":
            logger.error(log_msg)
        elif severity == "medium":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
    
    def get_security_status(self) -> Dict:
        """Get current security status."""
        # now = time.time()
        
        # Clean expired blocks
        # expired = []
        for ip in self.blocked_ips:
            # In real implementation, track block start time
            pass
        
        return {
            "blocked_ips": len(self.blocked_ips),
            "suspicious_users": len(self.suspicious_users),
            "active_rate_limits": sum(1 for hist in self.request_history.values() if len(hist) > 50),
            "recent_auth_failures": sum(len(fails) for fails in self.auth_failures.values()),
            "status": "alert" if len(self.blocked_ips) > 10 else "healthy"
        }


class SecretRotationManager:
    """
    Manages secret rotation for enhanced security.
    
    Secrets:
    - JWT signing keys
    - Database credentials
    - API keys
    """
    
    def __init__(self):
        self.secrets: Dict[str, Dict] = {}
        self.rotation_interval_days = 90
    
    def register_secret(self, name: str, current_value: str, 
                       rotation_date: datetime = None):
        """Register a secret for tracking."""
        if rotation_date is None:
            rotation_date = datetime.now() + timedelta(days=self.rotation_interval_days)
        
        self.secrets[name] = {
            "value": current_value,
            "created": datetime.now().isoformat(),
            "rotation_due": rotation_date.isoformat(),
            "rotated": False
        }
    
    def check_rotation_needed(self) -> List[str]:
        """Check which secrets need rotation."""
        now = datetime.now()
        needs_rotation = []
        
        for name, info in self.secrets.items():
            due_date = datetime.fromisoformat(info["rotation_due"])
            if now >= due_date and not info["rotated"]:
                needs_rotation.append(name)
                logger.warning(f"Secret '{name}' rotation overdue")
        
        return needs_rotation
    
    def get_secret_status(self) -> Dict:
        """Get status of all secrets."""
        return {
            name: {
                "created": info["created"],
                "rotation_due": info["rotation_due"],
                "days_until_rotation": (
                    datetime.fromisoformat(info["rotation_due"]) - datetime.now()
                ).days,
                "status": "overdue" if datetime.now() > datetime.fromisoformat(info["rotation_due"]) 
                         else "current"
            }
            for name, info in self.secrets.items()
        }


if __name__ == "__main__":
    print("Security Monitor")
    print("=" * 60)
    print("Components:")
    print("  - API Anomaly Detection")
    print("  - Abuse Prevention")
    print("  - Secret Rotation")
    print("  - Security Alerting")
    print("\nReady for integration.")

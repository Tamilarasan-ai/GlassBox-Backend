"""Security Event Logging System"""
from enum import Enum
from uuid import UUID
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SecurityEventType(str, Enum):
    """Types of security events"""
    FINGERPRINT_MISMATCH = "fingerprint_mismatch"
    IP_CHANGED = "ip_changed"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SESSION_HIJACKING_SUSPECTED = "session_hijacking_suspected"
    BLOCKED_USER_ACCESS_ATTEMPT = "blocked_user_access_attempt"


class SecurityEventLogger:
    """
    Logger for security events
    
    In production, these events should be sent to:
    - Database table for analysis
    - SIEM system (Splunk, DataDog, etc.)
    - Alert service (email, Slack, PagerDuty)
    """
    
    @staticmethod
    async def log_event(
        event_type: SecurityEventType,
        guest_user_id: UUID | str,
        details: dict
    ):
        """
        Log a security event
        
        Args:
            event_type: Type of security event
            guest_user_id: Guest user UUID involved
            details: Additional context about the event
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "guest_user_id": str(guest_user_id),
            **details
        }
        
        # Log at WARNING level for visibility
        logger.warning(f"SECURITY_EVENT: {event_type.value} | user={guest_user_id} | {details}")
        
        # TODO: In production, also:
        # 1. Insert into security_events table
        # 2. Send to monitoring service
        # 3. Trigger alerts for critical events
        
        return event


# Global singleton
security_logger = SecurityEventLogger()

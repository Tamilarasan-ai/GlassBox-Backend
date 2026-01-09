"""Shared Enums"""
import enum

class SessionStatus(str, enum.Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

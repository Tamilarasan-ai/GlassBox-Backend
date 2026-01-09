"""Rate Limiting Service - In-Memory Implementation"""
from datetime import datetime, timedelta
from typing import Dict
import asyncio
from collections import deque
import logging

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """
    In-memory rate limiter using sliding window algorithm
    
    Tracks requests per guest user with configurable limits.
    Note: State is lost on server restart.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        self.rpm = requests_per_minute
        self.rph = requests_per_hour
        self.requests: Dict[str, deque] = {}
        self._lock = asyncio.Lock()
    
    async def check_limit(self, key: str) -> tuple[bool, dict]:
        """
        Check if request is within rate limits
        
        Args:
            key: Unique key for rate limiting (e.g., "guest:uuid")
            
        Returns:
            Tuple of (allowed: bool, info: dict with limit details)
        """
        async with self._lock:
            now = datetime.utcnow()
            
            # Initialize deque for new keys
            if key not in self.requests:
                self.requests[key] = deque()
            
            requests = self.requests[key]
            
            # Remove old requests outside the windows
            cutoff_minute = now - timedelta(minutes=1)
            cutoff_hour = now - timedelta(hours=1)
            
            # Clean up requests older than 1 hour
            while requests and requests[0] < cutoff_hour:
                requests.popleft()
            
            # Count recent requests
            minute_count = sum(1 for ts in requests if ts >= cutoff_minute)
            hour_count = len(requests)
            
            # Check limits
            if minute_count >= self.rpm:
                reset_at = (cutoff_minute + timedelta(minutes=1)).isoformat()
                logger.warning(f"Rate limit (RPM) exceeded for {key}: {minute_count}/{self.rpm}")
                return False, {
                    "limit_type": "rpm",
                    "limit": self.rpm,
                    "remaining": 0,
                    "reset_at": reset_at
                }
            
            if hour_count >= self.rph:
                reset_at = (cutoff_hour + timedelta(hours=1)).isoformat()
                logger.warning(f"Rate limit (RPH) exceeded for {key}: {hour_count}/{self.rph}")
                return False, {
                    "limit_type": "rph",
                    "limit": self.rph,
                    "remaining": 0,
                    "reset_at": reset_at
                }
            
            # Add current request
            requests.append(now)
            
            return True, {
                "rpm_limit": self.rpm,
                "rpm_remaining": self.rpm - minute_count - 1,
                "rph_limit": self.rph,
                "rph_remaining": self.rph - hour_count - 1
            }
    
    def get_stats(self, key: str) -> dict:
        """Get current rate limit stats for a key"""
        if key not in self.requests:
            return {
                "rpm_used": 0,
                "rph_used": 0,
                "rpm_remaining": self.rpm,
                "rph_remaining": self.rph
            }
        
        now = datetime.utcnow()
        cutoff_minute = now - timedelta(minutes=1)
        requests = self.requests[key]
        
        minute_count = sum(1 for ts in requests if ts >= cutoff_minute)
        hour_count = len(requests)
        
        return {
            "rpm_used": minute_count,
            "rph_used": hour_count,
            "rpm_remaining": max(0, self.rpm - minute_count),
            "rph_remaining": max(0, self.rph - hour_count)
        }


# Global singleton instance (will be initialized from settings in real usage)
rate_limiter = InMemoryRateLimiter()

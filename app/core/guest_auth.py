"""Guest User Authentication Middleware - Enhanced with Phase 2 Security"""
from uuid import UUID
import logging

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.guest_user import GuestUser
from app.crud.crud_guest_user import get_or_create_guest_user
from app.core.config import settings
from app.core.fingerprint_matcher import calculate_similarity
from app.core.rate_limiter import rate_limiter
from app.core.security_events import security_logger, SecurityEventType

logger = logging.getLogger(__name__)

# Bearer token security scheme
guest_bearer = HTTPBearer(auto_error=False, scheme_name="GuestBearer")


async def authenticate_guest_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(guest_bearer),
    db: AsyncSession = Depends(get_db)
) -> GuestUser:
    """
    Authenticate guest user via Bearer token with Phase 2 security enhancements:
    - Rate limiting (60 RPM / 1000 RPH)
    - Device fingerprint fuzzy matching
    - IP change detection
    - Session hijacking detection
    
    Expected header: Authorization: Bearer {client_id}
    Optional header: X-Device-Fingerprint: {fingerprint_hash}
    
    Args:
        request: FastAPI request object
        credentials: Bearer token credentials
        db: Database session
        
    Returns:
        Authenticated GuestUser
        
    Raises:
        HTTPException: If token is missing, rate limited, or user is blocked
    """
    # Extract client_id from Bearer token
    if not credentials:
        logger.warning("Guest authentication failed: No bearer token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing guest token. Please provide Authorization: Bearer {client_id}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Parse client_id
    try:
        client_id = UUID(credentials.credentials)
        logger.debug(f"Guest authentication attempt: {client_id}")
    except ValueError:
        logger.warning(f"Invalid UUID format in bearer token: {credentials.credentials[:20]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid guest token format. Expected UUID.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Phase 2: Rate Limiting
    if settings.RATE_LIMIT_ENABLED:
        rate_key = f"guest:{client_id}"
        allowed, rate_info = await rate_limiter.check_limit(rate_key)
        
        if not allowed:
            # Log security event
            await security_logger.log_event(
                SecurityEventType.RATE_LIMIT_EXCEEDED,
                client_id,
                {
                    "limit_type": rate_info.get("limit_type"),
                    "limit": rate_info.get("limit"),
                    "reset_at": rate_info.get("reset_at")
                }
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again at {rate_info.get('reset_at')}",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(rate_info.get("limit")),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": rate_info.get("reset_at", "")
                }
            )
    
    # Extract metadata from request
    device_fp = request.headers.get("X-Device-Fingerprint")
    user_agent = request.headers.get("User-Agent", "")
    ip_address = request.client.host if request.client else "unknown"
    referrer = request.headers.get("Referer", "")
    
    user_metadata = {
        "ip": ip_address,
        "user_agent": user_agent,
        "referrer": referrer
    }
    
    # Get or create guest user
    logger.debug(f"Fetching/creating guest user for client_id: {client_id}")
    guest_user, created = await get_or_create_guest_user(
        db=db,
        client_id=client_id,
        device_fingerprint=device_fp,
        user_metadata=user_metadata
    )
    
    if created:
        logger.info(f"✓ New guest user created: {client_id}, session_count: {guest_user.session_count}")
    else:
        logger.debug(f"✓ Existing guest user authenticated: {client_id}, session_count: {guest_user.session_count}")
    
    # Security checks
    if guest_user.is_blocked:
        logger.warning(f"Blocked guest user attempted access: {client_id}")
        
        # Log security event
        await security_logger.log_event(
            SecurityEventType.BLOCKED_USER_ACCESS_ATTEMPT,
            guest_user.id,
            {
                "client_id": str(client_id),
                "blocked_reason": guest_user.blocked_reason,
                "ip": ip_address
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access blocked: {guest_user.blocked_reason or 'Account suspended'}"
        )
    
    # Phase 2: Device Fingerprint Fuzzy Matching
    if device_fp and guest_user.device_fingerprint:
        similarity = calculate_similarity(device_fp, guest_user.device_fingerprint)
        
        if similarity < settings.FINGERPRINT_MATCH_THRESHOLD:
            # Log security event
            await security_logger.log_event(
                SecurityEventType.FINGERPRINT_MISMATCH,
                guest_user.id,
                {
                    "stored_fp": guest_user.device_fingerprint[:16] + "...",
                    "provided_fp": device_fp[:16] + "...",
                    "similarity": round(similarity, 3),
                    "threshold": settings.FINGERPRINT_MATCH_THRESHOLD,
                    "ip": ip_address
                }
            )
            
            if settings.FINGERPRINT_STRICT_MODE:
                # Block the request in strict mode
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Device fingerprint verification failed. "
                           f"Similarity: {similarity:.1%}, Required: {settings.FINGERPRINT_MATCH_THRESHOLD:.1%}"
                )
    
    # Phase 2: IP Change Detection (Session Hijacking Indicator)
    if not created:  # Only for existing users
        last_ip = guest_user.user_metadata.get("ip")
        if last_ip and last_ip != ip_address:
            # Log IP change
            await security_logger.log_event(
                SecurityEventType.IP_CHANGED,
                guest_user.id,
                {
                    "old_ip": last_ip,
                    "new_ip": ip_address,
                    "session_count": guest_user.session_count,
                    "device_fp_match": device_fp == guest_user.device_fingerprint if device_fp else None
                }
            )
            
            # Update metadata with new IP and timestamp
            guest_user.user_metadata["previous_ip"] = last_ip
            guest_user.user_metadata["ip"] = ip_address
            guest_user.user_metadata["ip_changed_at"] = datetime.utcnow().isoformat()
            await db.commit()
    
    return guest_user

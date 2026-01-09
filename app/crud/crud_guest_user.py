"""CRUD operations for Guest Users"""
from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guest_user import GuestUser


async def get_guest_user_by_client_id(
    db: AsyncSession,
    client_id: UUID
) -> GuestUser | None:
    """
    Get guest user by client-generated UUID
    
    Args:
        db: Database session
        client_id: Client-generated cryptographic UUID
        
    Returns:
        GuestUser if found, None otherwise
    """
    result = await db.execute(
        select(GuestUser).where(GuestUser.client_id == client_id)
    )
    return result.scalar_one_or_none()


async def create_guest_user(
    db: AsyncSession,
    client_id: UUID,
    device_fingerprint: str | None = None,
    user_metadata: dict | None = None
) -> GuestUser:
    """
    Create a new guest user
    
    Args:
        db: Database session
        client_id: Client-generated UUID
        device_fingerprint: SHA-256 hash of browser characteristics
        user_metadata: User metadata (IP, user_agent, referrer, etc.)
        
    Returns:
        Created GuestUser
    """
    guest_user = GuestUser(
        client_id=client_id,
        device_fingerprint=device_fingerprint,
        user_metadata=user_metadata or {},
        first_seen_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        session_count=1
    )
    db.add(guest_user)
    await db.commit()
    await db.refresh(guest_user)
    return guest_user


async def update_last_seen(
    db: AsyncSession,
    guest_user: GuestUser
) -> GuestUser:
    """
    Update last_seen_at timestamp and increment session_count
    
    Args:
        db: Database session
        guest_user: GuestUser to update
        
    Returns:
        Updated GuestUser
    """
    guest_user.last_seen_at = datetime.utcnow()
    guest_user.session_count += 1
    await db.commit()
    await db.refresh(guest_user)
    return guest_user


async def get_or_create_guest_user(
    db: AsyncSession,
    client_id: UUID,
    device_fingerprint: str | None = None,
    user_metadata: dict | None = None
) -> tuple[GuestUser, bool]:
    """
    Get existing guest user or create new one
    
    Args:
        db: Database session
        client_id: Client-generated UUID
        device_fingerprint: Browser fingerprint hash
        user_metadata: User metadata
        
    Returns:
        Tuple of (GuestUser, created: bool)
    """
    guest_user = await get_guest_user_by_client_id(db, client_id)
    
    if guest_user:
        # Existing user - update last seen
        await update_last_seen(db, guest_user)
        return guest_user, False
    
    # New user - create
    guest_user = await create_guest_user(
        db=db,
        client_id=client_id,
        device_fingerprint=device_fingerprint,
        user_metadata=user_metadata
    )
    return guest_user, True


async def block_guest_user(
    db: AsyncSession,
    guest_user: GuestUser,
    reason: str
) -> GuestUser:
    """
    Block a guest user from accessing the system
    
    Args:
        db: Database session
        guest_user: GuestUser to block
        reason: Reason for blocking
        
    Returns:
        Updated GuestUser
    """
    guest_user.is_blocked = True
    guest_user.blocked_reason = reason
    await db.commit()
    await db.refresh(guest_user)
    return guest_user

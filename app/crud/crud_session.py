"""CRUD Operations for Sessions"""
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_session import Session
from app.models.enums import SessionStatus

logger = logging.getLogger(__name__)


async def get_or_create_session(
    db: AsyncSession,
    guest_user_id: UUID,
    user_input: str | None = None,
) -> Session:
    """
    Get existing active session for guest user or create new one
    This enables conversation history continuity
    
    Args:
        db: Database session
        guest_user_id: UUID of authenticated guest user
        user_input: Initial user input (for new sessions)
        
    Returns:
        Active session object
    """
    # Try to find an active session for this guest user
    result = await db.execute(
        select(Session)
        .where(
            Session.guest_user_id == guest_user_id,
            Session.is_active == True
        )
        .order_by(Session.created_at.desc())
        .limit(1)
    )
    existing_session = result.scalar_one_or_none()
    
    if existing_session:
        logger.info(f"✓ Reusing existing session: {existing_session.id} for guest {guest_user_id}")
        return existing_session
    
    # No active session, create new one
    logger.info(f"Creating new session for guest_user_id: {guest_user_id}")
    return await create_session(db, user_input or "New conversation", guest_user_id)


async def create_session(
    db: AsyncSession,
    user_input: str,
    guest_user_id: UUID | None = None,
) -> Session:
    """
    Create a new session (internal - use get_or_create_session for guest users)
    
    Args:
        db: Database session
        user_input: Initial user input
        guest_user_id: UUID of authenticated guest user
        
    Returns:
        Created session object
    """
    from app.models.agent import Agent
    
    # Get default agent (Calculator) or create if not exists
    result = await db.execute(select(Agent).where(Agent.slug == "calculator"))
    agent = result.scalar_one_or_none()
    
    if not agent:
        # Fallback for dev/testing if seed didn't run
        logger.warning("Calculator agent not found, creating fallback agent...")
        agent = Agent(
            name="Calculator Agent",
            slug="calculator",
            system_prompt="You are a helpful assistant.",
            model_config={"model": "gpt-4"}
        )
        db.add(agent)
        await db.flush()
        
    session = Session(
        user_id=str(guest_user_id) if guest_user_id else "anonymous",
        agent_id=agent.id,
        guest_user_id=guest_user_id,
        context_data={"initial_input": user_input},
        is_active=True
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    logger.info(f"✓ Session created: {session.id}, agent: {agent.id}")
    
    return session


async def get_session(
    db: AsyncSession,
    session_id: Any,
) -> Session | None:
    """
    Get session by ID with traces loaded
    
    Args:
        db: Database session
        session_id: Session ID (UUID)
        
    Returns:
        Session object with traces or None
    """
    result = await db.execute(
        select(Session)
        .options(selectinload(Session.traces))
        .where(Session.id == session_id)
    )
    
    return result.scalar_one_or_none()


async def update_session(
    db: AsyncSession,
    session_id: Any,
    final_response: str | None = None,
    status: SessionStatus | None = None,
) -> Session | None:
    """
    Update session status and response
    
    Args:
        db: Database session
        session_id: Session ID
        final_response: Final agent response
        status: New session status
        
    Returns:
        Updated session object
    """
    values = {}
    if final_response is not None:
        values["final_response"] = final_response
    if status is not None:
        values["status"] = status
        
    if not values:
        return await get_session(db, session_id)
        
    await db.execute(
        update(Session)
        .where(Session.id == session_id)
        .values(**values)
    )
    
    await db.commit()
    
    return await get_session(db, session_id)

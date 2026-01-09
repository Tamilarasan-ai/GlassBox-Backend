"""
Token Usage Analytics API - Using Existing trace_steps Schema
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps import DBSession, GuestUserDep
from app.crud import crud_token_usage

router = APIRouter()


@router.get("/analytics/tokens/me")
async def get_my_token_usage(
    db: DBSession,
    guest_user: GuestUserDep,
    days: int = 30
):
    """
    Get token usage statistics for current guest user
    
    Query params:
        days: Number of days to analyze (default: 30)
        
    Returns:
        - total_tokens: Total tokens used across all traces
        - total_cost_usd: Total cost in USD
        - trace_count: Number of traces
        - avg_tokens_per_trace: Average tokens per trace
    """
    
    stats = await crud_token_usage.get_guest_user_token_stats(
        db=db,
        guest_user_id=guest_user.id,
        days=days
    )
    
    return {
        "guest_user_id": str(guest_user.id),
        **stats
    }


@router.get("/analytics/tokens/session/{session_id}")
async def get_session_token_usage(
    session_id: UUID,
    db: DBSession,
):
    """
    Get token usage for a specific session
    
    Returns total tokens and cost for all traces in session
    """
    
    stats = await crud_token_usage.get_session_token_stats(
        db=db,
        session_id=session_id
    )
    
    return stats


@router.get("/analytics/tokens/trace/{trace_id}")
async def get_trace_token_breakdown(
    trace_id: UUID,
    db: DBSession,
):
    """
    Get detailed token breakdown for a trace
    
    Returns step-by-step token usage with costs
    """
    
    breakdown = await crud_token_usage.get_trace_token_breakdown(
        db=db,
        trace_id=trace_id
    )
    
    return breakdown


@router.get("/analytics/tokens/global")
async def get_global_token_stats(
    db: DBSession,
    days: int = 30
):
    """
    Get global token usage statistics
    
    Returns system-wide token and cost statistics
    """
    
    stats = await crud_token_usage.get_global_token_stats(
        db=db,
        days=days
    )
    
    return stats

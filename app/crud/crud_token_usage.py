"""
Token Usage Analytics - Using Existing trace_steps Table
"""
from uuid import UUID
from datetime import datetime, timedelta
from typing import Dict, Any
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trace_step import TraceStep
from app.models.trace import Trace


async def get_guest_user_token_stats(
    db: AsyncSession,
    guest_user_id: UUID,
    days: int = 30
) -> Dict[str, Any]:
    """
    Get aggregated token usage statistics for a guest user
    Uses existing trace_steps.tokens and cost_usd columns
    
    Returns:
        Dict with total_tokens, total_cost, request_count, etc.
    """
    
    since = datetime.utcnow() - timedelta(days=days)
    
    # Join trace_steps with traces to filter by guest_user
    result = await db.execute(
        select(
            func.sum(TraceStep.tokens).label("total_tokens"),
            func.sum(TraceStep.cost_usd).label("total_cost"),
            func.count(func.distinct(TraceStep.trace_id)).label("trace_count")
        )
        .join(Trace, TraceStep.trace_id == Trace.id)
        .join(Trace.session)
        .where(
            Trace.session.has(guest_user_id=guest_user_id),
            TraceStep.started_at >= since
        )
    )
    
    row = result.first()
    
    total_tokens = int(row.total_tokens or 0)
    total_cost = float(row.total_cost or Decimal('0.0'))
    trace_count = int(row.trace_count or 0)
    
    return {
        "period_days": days,
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 6),
        "trace_count": trace_count,
        "avg_tokens_per_trace": total_tokens // trace_count if trace_count else 0,
        "avg_cost_per_trace": round(total_cost / trace_count, 6) if trace_count else 0.0
    }


async def get_session_token_stats(
    db: AsyncSession,
    session_id: UUID
) -> Dict[str, Any]:
    """
    Get token usage statistics for a specific session
    """
    
    result = await db.execute(
        select(
            func.sum(TraceStep.tokens).label("total_tokens"),
            func.sum(TraceStep.cost_usd).label("total_cost"),
            func.count(TraceStep.id).label("step_count")
        )
        .join(Trace, TraceStep.trace_id == Trace.id)
        .where(Trace.session_id == session_id)
    )
    
    row = result.first()
    
    return {
        "session_id": str(session_id),
        "total_tokens": int(row.total_tokens or 0),
        "total_cost_usd": float(row.total_cost or Decimal('0.0')),
        "step_count": int(row.step_count or 0)
    }


async def get_trace_token_breakdown(
    db: AsyncSession,
    trace_id: UUID
) -> Dict[str, Any]:
    """
    Get detailed token breakdown for a trace (by step)
    """
    
    result = await db.execute(
        select(TraceStep)
        .where(TraceStep.trace_id == trace_id)
        .order_by(TraceStep.sequence_order)
    )
    
    steps = result.scalars().all()
    
    return {
        "trace_id": str(trace_id),
        "total_tokens": sum(step.tokens for step in steps),
        "total_cost_usd": float(sum(step.cost_usd for step in steps)),
        "steps": [
            {
                "sequence": step.sequence_order,
                "type": step.step_type,
                "name": step.step_name,
                "tokens": step.tokens,
                "cost_usd": float(step.cost_usd),
                "latency_ms": step.latency_ms
            }
            for step in steps
        ]
    }


async def get_global_token_stats(
    db: AsyncSession,
    days: int = 30
) -> Dict[str, Any]:
    """
    Get global token usage statistics across all users
    """
    
    since = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(
            func.sum(TraceStep.tokens).label("total_tokens"),
            func.sum(TraceStep.cost_usd).label("total_cost"),
            func.count(func.distinct(TraceStep.trace_id)).label("trace_count"),
            func.count(func.distinct(Trace.session_id)).label("session_count")
        )
        .join(Trace, TraceStep.trace_id == Trace.id)
        .where(TraceStep.started_at >= since)
    )
    
    row = result.first()
    
    total_tokens = int(row.total_tokens or 0)
    total_cost = float(row.total_cost or Decimal('0.0'))
    trace_count = int(row.trace_count or 0)
    
    return {
        "period_days": days,
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 6),
        "trace_count": trace_count,
        "session_count": int(row.session_count or 0),
        "avg_tokens_per_trace": total_tokens // trace_count if trace_count else 0
    }

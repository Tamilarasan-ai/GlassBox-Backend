"""CRUD Operations for Traces"""
import logging
from uuid import UUID
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.trace import Trace
from app.models.trace_step import TraceStep

logger = logging.getLogger(__name__)


async def create_trace(
    db: AsyncSession,
    session_id: UUID,
    agent_id: UUID,
    user_input: str,
    run_name: str | None = None,
) -> Trace:
    """
    Create a new trace
    
    Args:
        db: Database session
        session_id: Session ID
        agent_id: Agent ID
        user_input: User input
        run_name: Optional run name
        
    Returns:
        Created trace object
    """
    logger.debug(f"Creating trace for session {session_id}, agent {agent_id}")
    trace = Trace(
        session_id=session_id,
        agent_id=agent_id,
        user_input=user_input,
        run_name=run_name
    )
    logger.debug(f"Trace object created, saving to database...")
    
    db.add(trace)
    await db.commit()
    await db.refresh(trace)
    logger.info(f"✓ Trace created: {trace.id}")
    
    return trace


async def create_trace_step(
    db: AsyncSession,
    trace_id: UUID,
    sequence_order: int,
    step_type: str,
    step_name: str | None = None,
    input_payload: dict | None = None,
    output_payload: dict | None = None,
    latency_ms: int = 0,
) -> TraceStep:
    """
    Create a new atomic trace step
    """
    step = TraceStep(
        trace_id=trace_id,
        sequence_order=sequence_order,
        step_type=step_type,
        step_name=step_name,
        input_payload=input_payload,
        output_payload=output_payload,
        latency_ms=latency_ms,
    )
    
    db.add(step)
    await db.commit()
    await db.refresh(step)
    
    return step


async def update_trace_step(
    db: AsyncSession,
    step_id: UUID,
    latency_ms: int | None = None,
    tokens: int | None = None,
    cost_usd: float | None = None,
    completed_at: Any | None = None,
) -> TraceStep:
    """
    Update trace step with completion metrics
    
    Args:
        db: Database session
        step_id: Step ID to update
        latency_ms: Step execution time in milliseconds
        tokens: Tokens used for this step (LLM calls only)
        cost_usd: Cost for this step
        completed_at: Completion timestamp
        
    Returns:
        Updated step object
    """
    from decimal import Decimal
    
    step = await db.get(TraceStep, step_id)
    if not step:
        raise ValueError(f"TraceStep {step_id} not found")
    
    if latency_ms is not None:
        step.latency_ms = latency_ms
    
    if tokens is not None:
        step.tokens = tokens
    
    if cost_usd is not None:
        step.cost_usd = Decimal(str(cost_usd))
    
    if completed_at is not None:
        step.completed_at = completed_at
    
    await db.commit()
    await db.refresh(step)
    return step


async def update_trace(
    db: AsyncSession,
    trace_id: UUID,
    final_output: str | None = None,
    is_successful: bool = True,
    error_message: str | None = None,
    total_tokens: int = 0,
    total_cost: float = 0.0,
    latency_ms: int = 0,
    completed_at: Any | None = None,
) -> Trace:
    """
    Update trace with final results including metrics
    
    Args:
        db: Database session
        trace_id: Trace ID to update
        final_output: Final response text
        is_successful: Whether execution succeeded
        error_message: Error message if failed
        total_tokens: Total tokens used (input + output)
        total_cost: Total cost in USD
        latency_ms: Total latency in milliseconds
        completed_at: Completion timestamp
        
    Returns:
        Updated trace object
    """
    from decimal import Decimal
    
    trace = await db.get(Trace, trace_id)
    if not trace:
        raise ValueError(f"Trace {trace_id} not found")
        
    if final_output:
        trace.final_output = final_output
    
    trace.is_successful = is_successful
    if error_message:
        trace.error_message = error_message
        
    trace.total_tokens = total_tokens
    trace.total_cost = Decimal(str(total_cost))
    trace.latency_ms = latency_ms
    
    if completed_at:
        trace.completed_at = completed_at
    
    await db.commit()
    await db.refresh(trace)
    return trace


async def get_session_traces(
    db: AsyncSession,
    session_id: UUID,
) -> list[Trace]:
    """
    Get all traces for a session with steps loaded
    """
    result = await db.execute(
        select(Trace)
        .options(selectinload(Trace.steps))
        .where(Trace.session_id == session_id)
        .order_by(Trace.created_at.desc())
    )
    
    return list(result.scalars().all())


async def get_traces(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    session_id: UUID | None = None,
) -> list[Trace]:
    """
    Get paginated traces with optional session filter
    
    Args:
        db: Database session
        limit: Max traces to return (1-100)
        offset: Skip first N traces
        session_id: Filter by session (optional)
        
    Returns:
        List of traces ordered by created_at descending
    """
    query = select(Trace).order_by(Trace.created_at.desc())
    
    if session_id:
        query = query.where(Trace.session_id == session_id)
    
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())


async def count_traces(
    db: AsyncSession,
    session_id: UUID | None = None,
) -> int:
    """
    Count total traces with optional session filter
    
    Args:
        db: Database session
        session_id: Filter by session (optional)
        
    Returns:
        Total count of traces
    """
    from sqlalchemy import func
    
    query = select(func.count(Trace.id))
    
    if session_id:
        query = query.where(Trace.session_id == session_id)
    
    result = await db.execute(query)
    return result.scalar_one()


async def get_trace_with_steps(
    db: AsyncSession,
    trace_id: UUID,
) -> Trace | None:
    """
    Get trace with eagerly loaded steps
    
    Args:
        db: Database session
        trace_id: Trace ID
        
    Returns:
        Trace object with steps loaded, or None if not found
    """
    query = (
        select(Trace)
        .options(selectinload(Trace.steps))
        .where(Trace.id == trace_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_trace(
    db: AsyncSession,
    trace_id: UUID,
) -> Trace | None:
    """
    Get trace by ID (without steps)
    
    Args:
        db: Database session
        trace_id: Trace ID
        
    Returns:
        Trace object or None if not found
    """
    return await db.get(Trace, trace_id)

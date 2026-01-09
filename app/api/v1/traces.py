"""Traces API Endpoints"""
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Query

from app.api.deps import DBSession, APIKey
from app.schemas import trace as schemas
from app.schemas.session import SessionResponse
from app.crud import crud_session

router = APIRouter()


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    db: DBSession,
    api_key: APIKey,
) -> SessionResponse:
    """
    Get session with all traces
    
    Args:
        session_id: Session ID to retrieve
        db: Database session
        api_key: Validated API key
        
    Returns:
        SessionResponse with all traces
    """
    session = await crud_session.get_session(db=db, session_id=session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    return session


@router.get("/sessions/{session_id}/traces")
async def get_session_traces(
    session_id: UUID,
    db: DBSession,
    api_key: APIKey,
):
    """
    Get all traces for a session
    
    Args:
        session_id: Session ID
        db: Database session
        api_key: Validated API key
        
    Returns:
        List of traces ordered by step_number
    """
    session = await crud_session.get_session(db=db, session_id=session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    return {
        "session_id": session_id,
        "traces": sorted(session.traces, key=lambda t: t.created_at)
    }


@router.get("/traces", response_model=schemas.TraceListResponse)
async def list_traces(
    db: DBSession,
    api_key: APIKey,
    limit: int = Query(default=50, ge=1, le=100, description="Max traces to return"),
    offset: int = Query(default=0, ge=0, description="Skip first N traces"),
    session_id: UUID | None = Query(default=None, description="Filter by session ID"),
):
    """
    List all traces with pagination
    
    Query params:
    - limit: Max traces to return (1-100, default: 50)
    - offset: Skip first N traces (default: 0)
    - session_id: Filter by session (optional)
    
    Returns:
        Paginated list of traces with total count
    """
    from app.crud import crud_trace
    
    traces = await crud_trace.get_traces(
        db=db,
        limit=limit,
        offset=offset,
        session_id=session_id
    )
    
    total = await crud_trace.count_traces(db=db, session_id=session_id)
    
    return schemas.TraceListResponse(
        traces=[schemas.TraceResponse.model_validate(t) for t in traces],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/traces/{trace_id}", response_model=schemas.TraceDetailResponse)
async def get_trace_detail(
    trace_id: UUID,
    db: DBSession,
    api_key: APIKey,
):
    """
    Get trace with all steps nested
    
    Returns:
    - Full trace object
    - All trace_steps ordered by sequence_order
    - System prompt and model config snapshots
    """
    from app.crud import crud_trace
    
    trace = await crud_trace.get_trace_with_steps(db=db, trace_id=trace_id)
    
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace {trace_id} not found"
        )
    
    return schemas.TraceDetailResponse.model_validate(trace)


@router.post("/traces/{trace_id}/replay", response_model=schemas.ReplayResponse)
async def replay_trace(
    trace_id: UUID,
    db: DBSession,
    api_key: APIKey,
):
    """
    Replay a trace by re-running with same input
    
    Returns:
    - Original trace ID
    - New trace ID from replayed execution
    """
    from app.crud import crud_trace
    from app.engine.agent_engine import run_agent
    
    # Get original trace
    original = await crud_trace.get_trace(db=db, trace_id=trace_id)
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace {trace_id} not found"
        )
    
    # Re-run agent with same input
    result = await run_agent(
        db=db,
        session_id=original.session_id,
        user_input=original.user_input,
    )
    
    # Get the new trace (last one created for this session)
    traces = await crud_trace.get_session_traces(db=db, session_id=original.session_id)
    new_trace = traces[0]  # Most recent
    
    return schemas.ReplayResponse(
        original_trace_id=trace_id,
        new_trace_id=new_trace.id,
        message=f"Trace replayed successfully. Status: {result['status']}"
    )

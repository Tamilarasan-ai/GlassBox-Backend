"""
Streaming Chat Endpoint - Server-Sent Events
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.api.deps import DBSession, GuestUserDep
from app.schemas.chat import ChatRequest
from app.crud import crud_session
from app.engine.stream_engine import stream_agent_execution

router = APIRouter()


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    db: DBSession,
    guest_user: GuestUserDep,
):
    """
    Stream chat responses in real-time using Server-Sent Events (SSE)
    
    Events format:
    - data: {"type": "start", "session_id": "..."}
    - data: {"type": "tool_call", "name": "calculator", "args": {...}}
    - data: {"type": "tool_result", "result": "42"}
    - data: {"type": "response", "content": "The answer is 42"}
    - data: {"type": "complete", "success": true}
    
    Args:
        request: Chat message and options
        db: Database session
        guest_user: Authenticated guest user
        
    Returns:
        StreamingResponse with text/event-stream
    """
    try:
        # Get or create session for conversation history
        session = await crud_session.get_or_create_session(
            db=db,
            guest_user_id=guest_user.id,
            user_input=request.message,
        )
        
        async def event_generator():
            """Generate SSE events"""
            async for event in stream_agent_execution(
                db=db,
                session_id=session.id,
                user_input=request.message,
                max_iterations=request.max_iterations
            ):
                # Format as SSE
                yield f"data: {json.dumps(event)}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

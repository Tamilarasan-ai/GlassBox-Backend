"""Chat API Endpoints"""
import logging
from fastapi import APIRouter, HTTPException, status

from app.api.deps import DBSession, APIKey, GuestUserDep
from app.schemas.chat import ChatRequest, ChatResponse
from app.engine.agent_engine import run_agent
from app.crud import crud_session

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse, deprecated=True)
async def chat(
    request: ChatRequest,
    db: DBSession,
    api_key: APIKey,
    guest_user: GuestUserDep,
) -> ChatResponse:
    """
    [DEPRECATED] Execute agent loop for user message (synchronous)
    
    ⚠️ This endpoint is deprecated. Use POST /chat/stream for real-time streaming.
    
    Args:
        request: Chat request with user message
        db: Database session
        api_key: Validated API key
        guest_user: Authenticated guest user
        
    Returns:
        ChatResponse with agent's response and execution metadata
    """
    try:
        # Get or reuse existing session for conversation history
        session = await crud_session.get_or_create_session(
            db=db,
            guest_user_id=guest_user.id,
            user_input=request.message,
        )
        
        # Run agent loop
        result = await run_agent(
            db=db,
            session_id=session.id,
            user_input=request.message,
            max_iterations=request.max_iterations,
        )
        
        # Note: Trace is already updated by the agent engine
        # Session tracks the conversation, Trace tracks individual execution runs
        
        return ChatResponse(
            session_id=session.id,
            response=result["response"],
            steps_taken=result["steps_taken"],
            status=result["status"],
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Chat endpoint error for guest {guest_user.client_id}: {error_msg}", exc_info=True)
        
        # Check if it's a quota/rate limit error (user-friendly message)
        if "quota" in error_msg.lower() or "429" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_msg if "⚠️" in error_msg or "⏱️" in error_msg else "⚠️ API quota exceeded. Please try again later or upgrade your plan."
            )
        
        # Generic error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {error_msg}"
        )

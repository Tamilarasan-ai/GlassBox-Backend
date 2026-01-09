"""
Mock Streaming Endpoint - Test SSE Without API Quota
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json

from app.engine.mock_stream import mock_stream_agent_execution

router = APIRouter()


@router.post("/stream/mock")
async def mock_stream_chat(request: dict):
    """
    Mock streaming endpoint for testing SSE functionality
    WITHOUT using Gemini API quota
    
    Usage:
    POST /api/v1/chat/stream/mock
    {
        "message": "Calculate 5 + 3"
    }
    """
    
    message = request.get("message", "")
    session_id = "mock-session-123"
    
    async def event_generator():
        """Generate SSE events from mock engine"""
        async for event in mock_stream_agent_execution(
            session_id=session_id,
            user_input=message
        ):
            # Format as SSE
            yield f"data: {json.dumps(event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

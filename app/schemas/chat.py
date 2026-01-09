"""Chat API Schemas"""
from uuid import UUID
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for chat request"""
    message: str = Field(..., min_length=1, description="User message")
    user_id: str | None = Field(None, description="Optional user identifier")
    max_iterations: int | None = Field(None, gt=0, le=50, description="Max agent iterations")


class ChatResponse(BaseModel):
    """Schema for chat response"""
    session_id: UUID = Field(..., description="Session ID for tracking")
    response: str = Field(..., description="Agent's response")
    steps_taken: int = Field(..., description="Number of steps executed")
    status: str = Field(..., description="Completion status")

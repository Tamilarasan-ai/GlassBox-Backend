"""Session Pydantic Schemas"""
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.enums import SessionStatus
from app.schemas.trace import TraceResponse


class SessionBase(BaseModel):
    """Base session schema"""
    user_input: str = Field(..., description="User's input/query")
    user_id: str | None = Field(None, description="Optional user identifier")


class SessionCreate(SessionBase):
    """Schema for creating a session"""
    pass


class SessionUpdate(BaseModel):
    """Schema for updating a session"""
    final_response: str | None = None
    status: SessionStatus | None = None


class SessionResponse(SessionBase):
    """Schema for session responses"""
    id: int
    status: SessionStatus
    final_response: str | None
    created_at: datetime
    updated_at: datetime
    traces: list[TraceResponse] = []

    model_config = {"from_attributes": True}

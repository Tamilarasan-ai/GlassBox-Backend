"""Guest User Schemas"""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class GuestUserBase(BaseModel):
    """Base schema for guest user"""
    client_id: UUID = Field(..., description="Client-generated cryptographic UUID")
    device_fingerprint: str | None = Field(None, description="Device fingerprint hash")


class GuestUserCreate(GuestUserBase):
    """Schema for creating a guest user"""
    user_metadata: dict = Field(default_factory=dict, description="User metadata")


class GuestUserResponse(GuestUserBase):
    """Schema for guest user response"""
    id: UUID
    session_count: int
    first_seen_at: datetime
    last_seen_at: datetime
    is_blocked: bool
    
    model_config = {"from_attributes": True}


class GuestUserUpdate(BaseModel):
    """Schema for updating guest user"""
    device_fingerprint: str | None = None
    is_blocked: bool | None = None
    blocked_reason: str | None = None

"""Trace Pydantic Schemas"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field


# ============================================================
# Legacy Schemas (for backwards compatibility)
# ============================================================
class TraceBase(BaseModel):
    """Base trace schema (legacy)"""
    trace_type: str = Field(..., description="Type: 'thought' or 'tool_call'")
    content: str = Field(..., description="Trace content")
    trace_metadata: dict | None = Field(None, description="Additional metadata")
    step_number: int = Field(..., description="Step number in sequence")


class TraceCreate(TraceBase):
    """Schema for creating a trace (legacy)"""
    session_id: int


# ============================================================
# New Trace Schemas
# ============================================================
class TraceStepResponse(BaseModel):
    """Schema for trace step in responses"""
    id: UUID
    sequence_order: int
    step_type: str
    step_name: str | None
    input_payload: dict | None
    output_payload: dict | None
    latency_ms: int
    tokens: int
    cost_usd: Decimal
    is_error: bool
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class TraceResponse(BaseModel):
    """Schema for basic trace response (list view)"""
    id: UUID
    session_id: UUID
    agent_id: UUID
    user_input: str
    final_output: str | None
    run_name: str | None
    total_tokens: int
    total_cost: Decimal
    latency_ms: int
    is_successful: bool
    error_message: str | None
    system_prompt_snapshot: str | None
    model_config_snapshot: dict | None
    environment: str
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class TraceDetailResponse(BaseModel):
    """Schema for detailed trace response (with steps)"""
    id: UUID
    session_id: UUID
    agent_id: UUID
    user_input: str
    final_output: str | None
    run_name: str | None
    
    # Metrics
    total_tokens: int
    total_cost: Decimal
    latency_ms: int
    is_successful: bool
    error_message: str | None
    
    # Observability snapshots
    system_prompt_snapshot: str | None
    model_config_snapshot: dict | None
    tags: list[str]
    environment: str
    
    # Timestamps
    created_at: datetime
    completed_at: datetime | None
    
    # Nested steps
    steps: list[TraceStepResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class TraceListResponse(BaseModel):
    """Schema for paginated trace list"""
    traces: list[TraceResponse]
    total: int
    limit: int
    offset: int


class ReplayResponse(BaseModel):
    """Schema for replay response"""
    original_trace_id: UUID
    new_trace_id: UUID
    message: str

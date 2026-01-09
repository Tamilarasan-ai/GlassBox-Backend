"""TraceStep Model - Atomic observations in a trace"""
from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Text, Integer, ForeignKey, Boolean, Numeric, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.trace import Trace


class TraceStep(Base):
    """
    TraceStep model for atomic observations (Thoughts, Tool Calls, Results)
    """
    __tablename__ = "trace_steps"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    trace_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("traces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Ordering
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Classification
    step_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # thought, tool_call, etc.
    step_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Glass Box Content
    input_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    # Metrics
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=0.000000)
    
    # Error tracking
    is_error: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps (No TimestampMixin because we want specific started/completed)
    started_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    
    # Relationships
    trace: Mapped["Trace"] = relationship("Trace", back_populates="steps")

    def __repr__(self) -> str:
        return f"<TraceStep(id={self.id}, type={self.step_type}, order={self.sequence_order})>"

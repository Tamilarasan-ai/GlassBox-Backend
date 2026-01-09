"""Trace Model - Logs agent thoughts and tool executions"""
from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Text, Integer, ForeignKey, Boolean, Numeric, ARRAY, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.encrypted_types import EncryptedText

if TYPE_CHECKING:
    from app.models.chat_session import Session
    from app.models.agent import Agent
    from app.models.trace_step import TraceStep


class Trace(Base, TimestampMixin):
    """
    Trace model for logging agent execution steps
    
    Stores high-level run metrics, snapshots, and links to atomic steps.
    """
    __tablename__ = "traces"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    session_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    
    # Inputs/Outputs
    # Encrypted conversation data (Phase 2: Security Hardening)
    user_input: Mapped[str] = mapped_column(EncryptedText, nullable=False)
    final_output: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    run_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Metrics
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=0.000000)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status & Error Handling
    is_successful: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Glass Box Observability Snapshots
    system_prompt_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_config_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default=text("ARRAY[]::text[]"))
    environment: Mapped[str] = mapped_column(String(50), server_default="production", index=True)
    
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    
    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="traces")
    agent: Mapped["Agent"] = relationship("Agent")
    steps: Mapped[list["TraceStep"]] = relationship(
        "TraceStep",
        back_populates="trace",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Trace(id={self.id}, session_id={self.session_id})>"

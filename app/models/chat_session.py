"""Session Model - Represents an agent conversation session"""
from __future__ import annotations
from typing import TYPE_CHECKING
import enum
from datetime import datetime

from sqlalchemy import String, Text, Enum, ForeignKey, Boolean, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

from app.models.enums import SessionStatus

if TYPE_CHECKING:
    from app.models.trace import Trace
    from app.models.agent import Agent
    from app.models.guest_user import GuestUser


class Session(Base, TimestampMixin):
    """
    Session model representing an agent conversation
    
    Tracks the overall state and metadata for an agent execution
    """
    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    agent_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="RESTRICT"),
        nullable=False,
    )
    
    # Link to guest user (optional for backward compatibility)
    guest_user_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("guest_users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Guest user who created this session"
    )
    
    context_data: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_active_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )
    
    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="sessions")
    guest_user: Mapped["GuestUser | None"] = relationship(
        "GuestUser",
        back_populates="sessions",
        doc="Guest user who created this session"
    )
    traces: Mapped[list["Trace"]] = relationship(
        "Trace",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id})>"

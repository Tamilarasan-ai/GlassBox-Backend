"""Agent Model - Configuration and System Prompts"""
from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Boolean, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.chat_session import Session


class Agent(Base, TimestampMixin):
    """
    Agent configuration model
    
    Stores system prompts, model settings, and metadata for different agents.
    """
    __tablename__ = "agents"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    model_config: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Relationships
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="agent")

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, slug={self.slug})>"

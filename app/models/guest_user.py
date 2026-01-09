"""Guest User Model - Passwordless Guest Authentication"""
from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import datetime
from uuid import UUID as PyUUID

from sqlalchemy import String, Integer, Boolean, Text, text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.chat_session import Session


class GuestUser(Base, TimestampMixin):
    """
    Guest User model for passwordless authentication
    
    Uses cryptographic client-generated UUIDs with device fingerprinting
    for secure session tracking without traditional login.
    """
    __tablename__ = "guest_users"

    id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    
    # Client-generated cryptographic UUID
    client_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        index=True,
        comment="Client-generated UUID for guest identification"
    )
    
    # Device fingerprint for session hijacking detection
    device_fingerprint: Mapped[str | None] = mapped_column(
        String(64),
        index=True,
        comment="SHA-256 hash of browser characteristics"
    )
    
    # User metadata (IP, user agent, referrer)
    user_metadata: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="User metadata: IP, user_agent, referrer, etc."
    )
    
    # Session tracking
    first_seen_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        comment="First time this guest user was seen"
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
        comment="Last activity timestamp"
    )
    session_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
        comment="Number of sessions created by this guest"
    )
    
    # Security
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        comment="Whether this guest is blocked from access"
    )
    blocked_reason: Mapped[str | None] = mapped_column(
        Text,
        comment="Reason for blocking (abuse, rate limit, etc.)"
    )
    
    # Privacy & Compliance
    data_retention_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=90,
        server_default=text("90"),
        comment="Days before auto-deletion (GDPR compliance)"
    )
    consent_given: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        comment="Whether user gave consent for data tracking"
    )
    
    # Relationships
    sessions: Mapped[list["Session"]] = relationship(
        "Session",
        back_populates="guest_user",
        cascade="all, delete-orphan",
        doc="All sessions created by this guest user"
    )

    def __repr__(self) -> str:
        return f"<GuestUser(client_id={self.client_id}, sessions={self.session_count})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if guest data should be auto-deleted"""
        from datetime import timedelta
        expiry_date = self.last_seen_at + timedelta(days=self.data_retention_days)
        return datetime.utcnow() > expiry_date

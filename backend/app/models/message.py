"""
Message database model.

Stores individual chat messages with metadata about blocking status.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class MessageRole(str, enum.Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"


class Message(Base):
    """Chat message model."""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role = Column(SQLEnum(MessageRole, values_callable=lambda x: [e.value for e in x]), nullable=False)
    content = Column(Text, nullable=False)
    blocked = Column(Boolean, default=False, nullable=False)
    block_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, blocked={self.blocked})>"

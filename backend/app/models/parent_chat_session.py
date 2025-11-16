"""
Parent chat session database model.

Represents a conversation session between a parent and the AI.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ParentChatSession(Base):
    """Parent chat session model for grouping messages."""

    __tablename__ = "parent_chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("parents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title = Column(String(255), nullable=True, default="New Chat")
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    last_message_at = Column(DateTime, nullable=True)
    message_count = Column(Integer, default=0, nullable=False)

    # Relationships
    parent = relationship("Parent", back_populates="chat_sessions")
    messages = relationship(
        "ParentMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ParentMessage.created_at"
    )

    # Composite index for efficient queries
    __table_args__ = (
        Index('ix_parent_chat_sessions_parent_last_message', 'parent_id', 'last_message_at'),
    )

    def __repr__(self) -> str:
        return f"<ParentChatSession(id={self.id}, parent_id={self.parent_id}, title={self.title}, started_at={self.started_at})>"

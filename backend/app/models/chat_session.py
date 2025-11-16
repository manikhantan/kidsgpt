"""
Chat session database model.

Represents a conversation session between a child and the AI.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ChatSession(Base):
    """Chat session model for grouping messages."""

    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id = Column(
        UUID(as_uuid=True),
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title = Column(String(255), nullable=True, default="New Chat")
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    last_message_at = Column(DateTime, nullable=True)
    message_count = Column(Integer, default=0, nullable=False)

    # Relationships
    child = relationship("Child", back_populates="chat_sessions")
    messages = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )

    # Composite index for efficient queries
    __table_args__ = (
        Index('ix_chat_sessions_child_last_message', 'child_id', 'last_message_at'),
    )

    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, child_id={self.child_id}, title={self.title}, started_at={self.started_at})>"

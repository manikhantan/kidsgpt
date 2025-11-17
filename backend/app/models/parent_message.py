"""
Parent message database model.

Stores individual chat messages for parent conversations.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.message import MessageRole


class ParentMessage(Base):
    """Parent chat message model."""

    __tablename__ = "parent_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("parent_chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role = Column(SQLEnum(MessageRole, values_callable=lambda x: [e.value for e in x]), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("ParentChatSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<ParentMessage(id={self.id}, role={self.role})>"

"""
Message insight model for tracking per-message analytics.
"""
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class MessageInsight(Base):
    """Track analytics for individual messages."""
    __tablename__ = "message_insights"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, unique=True)
    topic = Column(String(100), nullable=True)
    is_learning_question = Column(Boolean, nullable=False, default=False)
    estimated_time_seconds = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationship
    message = relationship("Message", backref="insight", uselist=False)

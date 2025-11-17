"""
Child topic summary model for aggregated topic insights.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ChildTopicSummary(Base):
    """Aggregated topic insights for a child."""
    __tablename__ = "child_topic_summary"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    child_id = Column(UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(100), nullable=False)
    total_time_seconds = Column(Integer, nullable=False, default=0)
    message_count = Column(Integer, nullable=False, default=0)
    last_accessed = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('child_id', 'topic', name='uix_child_topic'),
    )

    # Relationship
    child = relationship("Child", backref="topic_summaries")

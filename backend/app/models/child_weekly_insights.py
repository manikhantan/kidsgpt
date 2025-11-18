"""
Child weekly insights model for weekly highlights.
"""
from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class ChildWeeklyInsights(Base):
    """Weekly insights summary for a child."""
    __tablename__ = "child_weekly_insights"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    child_id = Column(UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False)
    week_start = Column(Date, nullable=False)  # Start of the week (Monday)
    top_topics = Column(JSONB, nullable=False, default=[])  # List of {topic, time_seconds}
    total_learning_questions = Column(Integer, nullable=False, default=0)
    total_questions = Column(Integer, nullable=False, default=0)
    new_curiosities = Column(JSONB, nullable=False, default=[])  # Topics accessed for first time
    needs_support_topics = Column(JSONB, nullable=False, default=[])  # Topics with repeated questions
    suggested_discussion_topic = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('child_id', 'week_start', name='uix_child_week'),
    )

    # Relationship
    child = relationship("Child", backref="weekly_insights")

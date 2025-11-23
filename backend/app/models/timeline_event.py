"""
Timeline Event database model.

Represents significant learning accelerations and compression events.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class TimelineEvent(Base):
    """Timeline compression events for tracking learning acceleration."""

    __tablename__ = "timeline_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    future_identity_id = Column(
        UUID(as_uuid=True),
        ForeignKey("future_identities.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Event details
    concept_learned = Column(String(200), nullable=False)
    normal_learning_age = Column(Integer, nullable=False)  # When people usually learn this
    actual_age = Column(Integer, nullable=False)  # User's age when they learned it
    years_compressed = Column(Float, nullable=False)  # How many years ahead

    # Additional context
    complexity_score = Column(Float, nullable=True)  # AI-scored complexity (1-10)
    context = Column(Text, nullable=True)  # What triggered this event
    session_id = Column(UUID(as_uuid=True), nullable=True)  # Associated chat session

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    future_identity = relationship("FutureIdentity", back_populates="timeline_events")

    def __repr__(self) -> str:
        return f"<TimelineEvent(concept={self.concept_learned}, years_compressed={self.years_compressed})>"

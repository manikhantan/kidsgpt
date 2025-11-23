"""
Future Identity database model.

Represents a child's future identity profile for the Future Self AI feature.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class FutureIdentity(Base):
    """Future identity profile for a child user."""

    __tablename__ = "future_identities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id = Column(
        UUID(as_uuid=True),
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One future identity per child
        index=True
    )

    # Core future identity fields
    future_identity = Column(String(100), nullable=False)  # "Founder", "Creator", etc.
    breakthrough_age = Column(Integer, nullable=False)  # Age when they achieve breakthrough
    first_ambition = Column(String(500), nullable=False)  # What they want to be known for

    # Timeline tracking
    timeline_compression = Column(Float, default=0.0, nullable=False)  # Years ahead of schedule
    thinking_age = Column(Float, nullable=False)  # What age level they think at
    current_age = Column(Integer, nullable=False)  # Their actual age at profile creation

    # Trajectory tracking
    trajectory = Column(String(20), default="steady", nullable=False)  # accelerating/steady/stalled

    # Store revealed achievements as JSONB array
    revealed_achievements = Column(JSONB, default=list, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    child = relationship("Child", backref="future_identity")
    timeline_events = relationship(
        "TimelineEvent",
        back_populates="future_identity",
        cascade="all, delete-orphan"
    )
    future_slips = relationship(
        "FutureSlip",
        back_populates="future_identity",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<FutureIdentity(child_id={self.child_id}, identity={self.future_identity}, compression={self.timeline_compression})>"

"""
Future Slip database model.

Represents "accidental" revelations about the user's future achievements.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class FutureSlipType(str, enum.Enum):
    """Types of future slips that can occur."""
    ACHIEVEMENT = "achievement"
    EVENT = "event"
    CREATION = "creation"
    TED_TALK = "ted_talk"
    PATENT = "patent"
    COMPANY = "company"
    BREAKTHROUGH = "breakthrough"
    INNOVATION = "innovation"


class FutureSlip(Base):
    """Future slip - accidental revelation of future achievement."""

    __tablename__ = "future_slips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    future_identity_id = Column(
        UUID(as_uuid=True),
        ForeignKey("future_identities.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Slip details
    slip_type = Column(
        SQLEnum(FutureSlipType, name="future_slip_type"),
        nullable=False
    )
    content = Column(Text, nullable=False)  # What was revealed
    supposed_year = Column(Integer, nullable=False)  # When it "happens" in their future
    context = Column(Text, nullable=True)  # What triggered the slip

    # Associated session
    session_id = Column(UUID(as_uuid=True), nullable=True)  # Chat session where slip occurred
    message_id = Column(UUID(as_uuid=True), nullable=True)  # Specific message

    # Timestamp
    revealed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    future_identity = relationship("FutureIdentity", back_populates="future_slips")

    def __repr__(self) -> str:
        return f"<FutureSlip(type={self.slip_type}, year={self.supposed_year})>"

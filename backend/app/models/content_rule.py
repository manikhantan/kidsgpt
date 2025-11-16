"""
Content rule database model.

Stores content filtering rules (allowlist or blocklist) for each parent.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ContentRuleMode(str, enum.Enum):
    """Content rule mode enumeration."""
    ALLOWLIST = "allowlist"
    BLOCKLIST = "blocklist"


class ContentRule(Base):
    """Content rule model for parent's content filtering settings."""

    __tablename__ = "content_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("parents.id", ondelete="CASCADE"),
        unique=True,  # One rule set per parent
        nullable=False
    )
    mode = Column(
        SQLEnum(ContentRuleMode),
        nullable=False,
        default=ContentRuleMode.BLOCKLIST
    )
    # JSON arrays for flexible topic/keyword storage
    topics = Column(JSONB, nullable=False, default=list)
    keywords = Column(JSONB, nullable=False, default=list)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    parent = relationship("Parent", back_populates="content_rules")

    def __repr__(self) -> str:
        return f"<ContentRule(id={self.id}, parent_id={self.parent_id}, mode={self.mode})>"

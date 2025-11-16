"""
Parent database model.

Represents a parent user who can create child accounts and set content rules.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Parent(Base):
    """Parent user model."""

    __tablename__ = "parents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    children = relationship(
        "Child",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    content_rules = relationship(
        "ContentRule",
        back_populates="parent",
        uselist=False,  # One-to-one relationship
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Parent(id={self.id}, email={self.email}, name={self.name})>"

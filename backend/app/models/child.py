"""
Child database model.

Represents a child user who can chat with the AI within parent-defined rules.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Child(Base):
    """Child user model."""

    __tablename__ = "children"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("parents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
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
    parent = relationship("Parent", back_populates="children")
    chat_sessions = relationship(
        "ChatSession",
        back_populates="child",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Child(id={self.id}, username={self.username}, name={self.name})>"

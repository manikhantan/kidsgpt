"""
Parent-related schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class ParentBase(BaseModel):
    """Base parent schema."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)


class ParentCreate(ParentBase):
    """Schema for creating a parent."""
    password: str = Field(..., min_length=8, max_length=100)


class ParentUpdate(BaseModel):
    """Schema for updating parent info."""
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class ParentResponse(ParentBase):
    """Schema for parent response."""
    id: UUID
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class ParentAnalytics(BaseModel):
    """Schema for parent analytics about a child."""
    child_id: UUID
    child_name: str
    total_sessions: int
    total_messages: int
    blocked_messages: int
    last_activity: Optional[datetime]

"""
Child-related schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class ChildBase(BaseModel):
    """Base child schema."""
    username: str = Field(..., min_length=3, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)


class ChildCreate(ChildBase):
    """Schema for creating a child account."""
    password: str = Field(..., min_length=6, max_length=100)


class ChildUpdate(BaseModel):
    """Schema for updating child info."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=6, max_length=100)


class ChildResponse(ChildBase):
    """Schema for child response (parent view)."""
    id: UUID
    parent_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChildProfile(BaseModel):
    """Schema for child's own profile."""
    id: UUID
    username: str
    name: str

    class Config:
        from_attributes = True

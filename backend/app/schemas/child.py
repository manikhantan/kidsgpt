"""
Child-related schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class ChildBase(BaseModel):
    """Base child schema."""
    email: EmailStr
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
    parent_id: UUID = Field(..., alias="parentId")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class ChildProfile(BaseModel):
    """Schema for child's own profile."""
    id: UUID
    email: str
    name: str

    class Config:
        from_attributes = True

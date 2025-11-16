"""
Content rule schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import List
from app.models.content_rule import ContentRuleMode


class ContentRuleBase(BaseModel):
    """Base content rule schema."""
    mode: ContentRuleMode = ContentRuleMode.BLOCKLIST
    topics: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)


class ContentRuleCreate(ContentRuleBase):
    """Schema for creating content rules."""
    pass


class ContentRuleUpdate(BaseModel):
    """Schema for updating content rules."""
    mode: ContentRuleMode = ContentRuleMode.BLOCKLIST
    topics: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)


class ContentRuleResponse(ContentRuleBase):
    """Schema for content rule response."""
    id: UUID
    parent_id: UUID
    updated_at: datetime

    class Config:
        from_attributes = True

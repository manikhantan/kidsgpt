"""
Parent chat session and message schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import List, Optional
from app.models.message import MessageRole


class ParentChatMessageRequest(BaseModel):
    """Schema for parent sending a chat message."""
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[UUID] = Field(None, description="Optional session ID to add message to", alias="sessionId")


class ParentMessageResponse(BaseModel):
    """Schema for a single parent message response."""
    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ParentChatResponse(BaseModel):
    """Schema for parent chat response after sending a message."""
    user_message: ParentMessageResponse
    assistant_message: Optional[ParentMessageResponse] = None
    session_id: Optional[UUID] = Field(None, description="The session this message belongs to")
    session_title: Optional[str] = Field(None, description="AI-generated title for the session")


class ParentChatSessionSummary(BaseModel):
    """Schema for a parent chat session summary (for listing)."""
    id: UUID
    title: str
    started_at: datetime
    last_message_at: datetime
    message_count: int
    preview: Optional[str] = Field(None, description="First ~100 chars of first user message")

    class Config:
        from_attributes = True


class PaginatedParentChatSessions(BaseModel):
    """Schema for paginated parent chat sessions response."""
    sessions: List[ParentChatSessionSummary]
    total: int = Field(..., description="Total number of sessions")
    page: int
    page_size: int
    has_more: bool = Field(..., description="True if more pages exist")


class FullParentChatSession(BaseModel):
    """Schema for a full parent chat session with all messages."""
    id: UUID
    parent_id: UUID
    title: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    messages: List[ParentMessageResponse]
    last_message_at: Optional[datetime] = None
    message_count: Optional[int] = None

    class Config:
        from_attributes = True


class CreateParentChatSessionResponse(BaseModel):
    """Schema for a newly created parent chat session."""
    id: UUID
    parent_id: UUID
    title: str
    started_at: datetime
    messages: List[ParentMessageResponse] = []

    class Config:
        from_attributes = True

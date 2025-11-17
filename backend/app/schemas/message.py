"""
Message and chat session schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import List, Optional
from app.models.message import MessageRole


class ChatMessageRequest(BaseModel):
    """Schema for sending a chat message."""
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[UUID] = Field(None, description="Optional session ID to add message to", alias="sessionId")


class MessageResponse(BaseModel):
    """Schema for a single message response."""
    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    blocked: bool
    block_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """Schema for chat response after sending a message."""
    user_message: MessageResponse
    assistant_message: Optional[MessageResponse] = None
    was_blocked: bool = False
    block_reason: Optional[str] = None
    session_id: Optional[UUID] = Field(None, description="The session this message belongs to")
    session_title: Optional[str] = Field(None, description="AI-generated title for the session")


class ChatSessionSummary(BaseModel):
    """Schema for a chat session summary (for listing)."""
    id: UUID
    title: str
    started_at: datetime
    last_message_at: datetime
    message_count: int
    preview: Optional[str] = Field(None, description="First ~100 chars of first user message")

    class Config:
        from_attributes = True


class PaginatedChatSessions(BaseModel):
    """Schema for paginated chat sessions response."""
    sessions: List[ChatSessionSummary]
    total: int = Field(..., description="Total number of sessions")
    page: int
    page_size: int
    has_more: bool = Field(..., description="True if more pages exist")


class FullChatSession(BaseModel):
    """Schema for a full chat session with all messages."""
    id: UUID
    child_id: UUID
    title: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    messages: List[MessageResponse]
    last_message_at: Optional[datetime] = None
    message_count: Optional[int] = None

    class Config:
        from_attributes = True


class CreateChatSessionRequest(BaseModel):
    """Schema for creating a new chat session (empty body)."""
    pass


class CreateChatSessionResponse(BaseModel):
    """Schema for a newly created chat session."""
    id: UUID
    child_id: UUID
    title: str
    started_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    """Schema for a chat session with messages."""
    id: UUID
    child_id: UUID
    started_at: datetime
    ended_at: Optional[datetime]
    messages: List[MessageResponse]

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Schema for chat history response."""
    sessions: List[ChatSessionResponse]
    total_sessions: int
    total_messages: int

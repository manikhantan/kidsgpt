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

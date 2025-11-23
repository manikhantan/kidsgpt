"""
Future Self AI schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import List, Optional, Literal
from app.models.future_slip import FutureSlipType


class FutureIdentityRequest(BaseModel):
    """Schema for creating a future identity profile."""
    future_identity: str = Field(..., min_length=1, max_length=100, description="Founder, Creator, Healer, Builder, Discoverer, Changemaker, or custom")
    breakthrough_age: int = Field(..., ge=14, le=30, description="Age when they achieve their first breakthrough")
    first_ambition: str = Field(..., min_length=1, max_length=500, description="What they want to be known for")
    current_age: int = Field(..., ge=5, le=18, description="User's current age")


class FutureIdentityResponse(BaseModel):
    """Schema for future identity profile response."""
    id: UUID
    child_id: UUID
    future_identity: str
    breakthrough_age: int
    first_ambition: str
    timeline_compression: float
    thinking_age: float
    current_age: int
    trajectory: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TimelineStatusResponse(BaseModel):
    """Schema for timeline status response."""
    future_identity: str
    current_age: int
    thinking_age: float
    timeline_compression: float
    trajectory: Literal["accelerating", "steady", "stalled"]
    breakthrough_age: int
    recent_milestones: List[dict] = Field(default_factory=list, description="Recent learning accelerations")


class TimelineUpdateData(BaseModel):
    """Schema for timeline update data in chat response."""
    years_compressed: float = Field(..., description="How many years this conversation saved")
    new_thinking_age: float
    concepts_accelerated: List[str] = Field(default_factory=list)


class FutureSlipData(BaseModel):
    """Schema for future slip data in chat response."""
    type: FutureSlipType
    content: str
    year_it_happens: int


class FutureModeChatResponse(BaseModel):
    """Schema for chat response in future mode."""
    message: str
    timeline_update: TimelineUpdateData
    future_slip: Optional[FutureSlipData] = None


class CompressionEventRequest(BaseModel):
    """Schema for logging a compression event."""
    concept_learned: str = Field(..., min_length=1, max_length=200)
    normal_learning_age: int = Field(..., ge=5, le=50)
    actual_age: int = Field(..., ge=5, le=18)
    years_compressed: float = Field(..., ge=0)
    complexity_score: Optional[float] = Field(None, ge=1, le=10)
    context: Optional[str] = None
    session_id: Optional[UUID] = None


class CompressionEventResponse(BaseModel):
    """Schema for compression event response."""
    id: UUID
    future_identity_id: UUID
    concept_learned: str
    normal_learning_age: int
    actual_age: int
    years_compressed: float
    complexity_score: Optional[float]
    context: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class RevealedAchievementResponse(BaseModel):
    """Schema for a revealed achievement/future slip."""
    id: UUID
    type: FutureSlipType
    content: str
    revealed_at: datetime
    supposed_year: int
    context: Optional[str]

    class Config:
        from_attributes = True


class RevealedAchievementsResponse(BaseModel):
    """Schema for all revealed achievements."""
    achievements: List[RevealedAchievementResponse]


class TimelineRecalculateRequest(BaseModel):
    """Schema for timeline recalculation request (empty body)."""
    pass


class TimelineRecalculateResponse(BaseModel):
    """Schema for timeline recalculation response."""
    timeline_compression: float
    thinking_age: float
    trajectory: str
    events_analyzed: int
    concepts_identified: int

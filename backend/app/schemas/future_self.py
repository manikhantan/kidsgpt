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
    future_identity: str = Field(..., min_length=1, max_length=100, description="Founder, Creator, Healer, Builder, Discoverer, Changemaker, or custom", alias="type")
    breakthrough_age: int = Field(..., ge=14, le=30, description="Age when they achieve their first breakthrough", alias="breakthroughAge")
    first_ambition: str = Field(..., min_length=1, max_length=500, description="What they want to be known for", alias="ambition")
    current_age: int = Field(..., ge=5, le=18, description="User's current age", alias="currentAge")


class FutureIdentityResponse(BaseModel):
    """Schema for future identity profile response."""
    id: UUID
    child_id: UUID = Field(..., alias="childId")
    future_identity: str = Field(..., alias="futureIdentity")
    breakthrough_age: int = Field(..., alias="breakthroughAge")
    first_ambition: str = Field(..., alias="firstAmbition")
    timeline_compression: float = Field(..., alias="timelineCompression")
    thinking_age: float = Field(..., alias="thinkingAge")
    current_age: int = Field(..., alias="currentAge")
    trajectory: str
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True  # Allow reading from ORM snake_case attributes


class TimelineStatusResponse(BaseModel):
    """Schema for timeline status response."""
    future_identity: str = Field(..., alias="futureIdentity")
    current_age: int = Field(..., alias="currentAge")
    thinking_age: float = Field(..., alias="thinkingAge")
    timeline_compression: float = Field(..., alias="timelineCompression")
    trajectory: Literal["accelerating", "steady", "stalled"]
    breakthrough_age: int = Field(..., alias="breakthroughAge")
    recent_milestones: List[dict] = Field(default_factory=list, description="Recent learning accelerations", alias="recentMilestones")

    class Config:
        populate_by_name = True  # Allow reading from mixed sources


class TimelineUpdateData(BaseModel):
    """Schema for timeline update data in chat response."""
    years_compressed: float = Field(..., description="How many years this conversation saved", alias="yearsCompressed")
    new_thinking_age: float = Field(..., alias="newThinkingAge")
    concepts_accelerated: List[str] = Field(default_factory=list, alias="conceptsAccelerated")


class FutureSlipData(BaseModel):
    """Schema for future slip data in chat response."""
    type: FutureSlipType
    content: str
    year_it_happens: int = Field(..., alias="yearItHappens")


class FutureModeChatResponse(BaseModel):
    """Schema for chat response in future mode."""
    message: str
    timeline_update: TimelineUpdateData
    future_slip: Optional[FutureSlipData] = None


class CompressionEventRequest(BaseModel):
    """Schema for logging a compression event."""
    concept_learned: str = Field(..., min_length=1, max_length=200, alias="conceptLearned")
    normal_learning_age: int = Field(..., ge=5, le=50, alias="normalLearningAge")
    actual_age: int = Field(..., ge=5, le=18, alias="actualAge")
    years_compressed: float = Field(..., ge=0, alias="yearsCompressed")
    complexity_score: Optional[float] = Field(None, ge=1, le=10, alias="complexityScore")
    context: Optional[str] = None
    session_id: Optional[UUID] = Field(None, alias="sessionId")


class CompressionEventResponse(BaseModel):
    """Schema for compression event response."""
    id: UUID
    future_identity_id: UUID = Field(..., alias="futureIdentityId")
    concept_learned: str = Field(..., alias="conceptLearned")
    normal_learning_age: int = Field(..., alias="normalLearningAge")
    actual_age: int = Field(..., alias="actualAge")
    years_compressed: float = Field(..., alias="yearsCompressed")
    complexity_score: Optional[float] = Field(None, alias="complexityScore")
    context: Optional[str]
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        from_attributes = True
        populate_by_name = True  # Allow reading from ORM snake_case attributes


class RevealedAchievementResponse(BaseModel):
    """Schema for a revealed achievement/future slip."""
    id: UUID
    type: FutureSlipType
    content: str
    revealed_at: datetime = Field(..., alias="revealedAt")
    supposed_year: int = Field(..., alias="supposedYear")
    context: Optional[str]

    class Config:
        from_attributes = True
        populate_by_name = True  # Allow reading from ORM snake_case attributes


class RevealedAchievementsResponse(BaseModel):
    """Schema for all revealed achievements."""
    achievements: List[RevealedAchievementResponse]


class TimelineRecalculateRequest(BaseModel):
    """Schema for timeline recalculation request (empty body)."""
    pass


class TimelineRecalculateResponse(BaseModel):
    """Schema for timeline recalculation response."""
    timeline_compression: float = Field(..., alias="timelineCompression")
    thinking_age: float = Field(..., alias="thinkingAge")
    trajectory: str
    events_analyzed: int = Field(..., alias="eventsAnalyzed")
    concepts_identified: int = Field(..., alias="conceptsIdentified")

    class Config:
        populate_by_name = True  # Allow reading from dict with snake_case keys

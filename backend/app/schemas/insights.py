"""
Schemas for parent insights dashboard.
"""
from pydantic import BaseModel, Field
from datetime import datetime, date
from uuid import UUID
from typing import Optional, List


class TopicInsight(BaseModel):
    """Information about a single topic of interest."""
    topic: str
    total_time_minutes: int = Field(..., description="Total time spent on this topic in minutes")
    message_count: int = Field(..., description="Number of messages about this topic")
    last_accessed: datetime


class LearningMetrics(BaseModel):
    """Metrics about learning behavior."""
    total_questions: int = Field(..., description="Total number of questions asked")
    learning_questions: int = Field(..., description="Questions with why/how (showing learning intent)")
    learning_percentage: float = Field(..., description="Percentage of learning questions (0-100)")
    learning_streak_days: int = Field(..., description="Number of consecutive days with learning activity")


class WeeklyHighlight(BaseModel):
    """Weekly highlight for the child."""
    week_start: date
    top_interests: List[TopicInsight] = Field(..., description="Top topics with time spent")
    academic_focus: Optional[str] = Field(None, description="Primary academic focus this week")
    new_curiosity: Optional[str] = Field(None, description="New topic explored for the first time")
    needs_support: Optional[str] = Field(None, description="Topic where child may need help")
    suggested_dinner_topic: Optional[str] = Field(None, description="Suggested conversation topic for parents")


class ChildInsightsDashboard(BaseModel):
    """Complete insights dashboard for a child."""
    child_id: UUID
    child_name: str

    # Top interests (top 5 topics)
    top_interests: List[TopicInsight] = Field(..., description="Top 5 topics the child finds interesting")

    # Learning metrics
    learning_metrics: LearningMetrics = Field(..., description="Learning behavior metrics")

    # Weekly highlights
    weekly_highlights: Optional[WeeklyHighlight] = Field(None, description="This week's highlights")

    # Summary stats
    total_sessions: int = Field(..., description="Total number of chat sessions")
    total_engagement_minutes: int = Field(..., description="Total estimated engagement time in minutes")
    last_activity: Optional[datetime] = Field(None, description="When the child was last active")

    class Config:
        from_attributes = True


class TopicSummaryResponse(BaseModel):
    """Response for a single topic summary."""
    topic: str
    total_time_minutes: int
    message_count: int
    last_accessed: datetime

    class Config:
        from_attributes = True


class InsightsSummary(BaseModel):
    """Simple summary of insights without weekly details."""
    child_id: UUID
    child_name: str
    top_interests: List[TopicSummaryResponse]
    learning_percentage: float
    total_sessions: int
    last_activity: Optional[datetime]

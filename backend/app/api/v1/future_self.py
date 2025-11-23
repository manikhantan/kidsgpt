"""
Future Self AI API endpoints.

Handles future identity setup, timeline tracking, and future mode features.
"""
from datetime import datetime
from uuid import UUID
from typing import Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.api.deps import get_db, get_current_kid
from app.models import Child, FutureIdentity, TimelineEvent, FutureSlip
from app.schemas.future_self import (
    FutureIdentityRequest,
    FutureIdentityResponse,
    TimelineStatusResponse,
    CompressionEventRequest,
    CompressionEventResponse,
    RevealedAchievementsResponse,
    RevealedAchievementResponse,
    TimelineRecalculateRequest,
    TimelineRecalculateResponse,
)
from app.services.future_self_service import FutureSelfService
from app.core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/kid", tags=["future-self"])


@router.get(
    "/future-identity",
    response_model=FutureIdentityResponse,
    summary="Get user's future identity profile",
    description="Retrieve the user's future identity profile if it exists."
)
async def get_future_identity(
    kid: Child = Depends(get_current_kid),
    db: Session = Depends(get_db)
) -> FutureIdentityResponse:
    """
    Get user's future identity profile.

    Returns:
        Future identity profile or 404 if not found
    """
    future_identity = db.query(FutureIdentity).filter(
        FutureIdentity.child_id == kid.id
    ).first()

    if not future_identity:
        raise NotFoundError("Future identity not found. Set up your future profile first.")

    return future_identity


@router.post(
    "/future-identity",
    response_model=FutureIdentityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Set up user's future identity profile",
    description="Create a future identity profile for the user to enable Future Self AI mode."
)
async def create_future_identity(
    data: FutureIdentityRequest,
    kid: Child = Depends(get_current_kid),
    db: Session = Depends(get_db)
) -> FutureIdentityResponse:
    """
    Set up user's future identity profile.

    This initializes the Future Self AI mode with:
    - Future identity (Founder, Creator, etc.)
    - Breakthrough age
    - First ambition
    - Initial timeline metrics

    Returns:
        Created future identity profile
    """
    # Check if future identity already exists
    existing = db.query(FutureIdentity).filter(
        FutureIdentity.child_id == kid.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Future identity already exists for this user. Update it instead."
        )

    # Create future identity
    future_identity = FutureIdentity(
        child_id=kid.id,
        future_identity=data.future_identity,
        breakthrough_age=data.breakthrough_age,
        first_ambition=data.first_ambition,
        current_age=data.current_age,
        timeline_compression=0.0,
        thinking_age=float(data.current_age + 1),  # Start 1 year ahead
        trajectory="steady",
        revealed_achievements=[]
    )

    db.add(future_identity)
    db.commit()
    db.refresh(future_identity)

    logger.info(f"Created future identity for child {kid.id}: {data.future_identity}")

    return future_identity


@router.get(
    "/timeline-status",
    response_model=TimelineStatusResponse,
    summary="Get user's timeline status",
    description="Retrieve current timeline metrics including compression, thinking age, and trajectory."
)
async def get_timeline_status(
    kid: Child = Depends(get_current_kid),
    db: Session = Depends(get_db)
) -> TimelineStatusResponse:
    """
    Get user's current timeline metrics.

    Returns:
        Timeline status with all current metrics
    """
    future_identity = db.query(FutureIdentity).filter(
        FutureIdentity.child_id == kid.id
    ).first()

    if not future_identity:
        raise NotFoundError("Future identity not found. Please set up your future profile first.")

    # Get recent milestones (last 10)
    recent_events = db.query(TimelineEvent).filter(
        TimelineEvent.future_identity_id == future_identity.id
    ).order_by(desc(TimelineEvent.created_at)).limit(10).all()

    recent_milestones = [
        {
            "concept": event.concept_learned,
            "yearsSaved": event.years_compressed
        }
        for event in recent_events
    ]

    return TimelineStatusResponse(
        future_identity=future_identity.future_identity,
        current_age=future_identity.current_age,
        thinking_age=future_identity.thinking_age,
        timeline_compression=future_identity.timeline_compression,
        trajectory=future_identity.trajectory,  # type: ignore
        breakthrough_age=future_identity.breakthrough_age,
        recent_milestones=recent_milestones
    )


@router.post(
    "/timeline/compression-event",
    response_model=CompressionEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a timeline compression event",
    description="Record a significant learning acceleration event."
)
async def create_compression_event(
    data: CompressionEventRequest,
    kid: Child = Depends(get_current_kid),
    db: Session = Depends(get_db)
) -> CompressionEventResponse:
    """
    Log a significant learning acceleration event.

    This records when the user learns something ahead of schedule
    and updates their timeline metrics accordingly.

    Returns:
        Created compression event
    """
    future_identity = db.query(FutureIdentity).filter(
        FutureIdentity.child_id == kid.id
    ).first()

    if not future_identity:
        raise NotFoundError("Future identity not found. Please set up your future profile first.")

    # Create timeline event
    event = TimelineEvent(
        future_identity_id=future_identity.id,
        concept_learned=data.concept_learned,
        normal_learning_age=data.normal_learning_age,
        actual_age=data.actual_age,
        years_compressed=data.years_compressed,
        complexity_score=data.complexity_score,
        context=data.context,
        session_id=data.session_id
    )

    db.add(event)

    # Update future identity metrics
    service = FutureSelfService()
    new_thinking_age = service.update_thinking_age(
        future_identity,
        data.years_compressed,
        db
    )
    future_identity.thinking_age = new_thinking_age
    future_identity.timeline_compression += data.years_compressed
    future_identity.trajectory = service.calculate_trajectory(future_identity, db)

    db.commit()
    db.refresh(event)

    logger.info(f"Created compression event for child {kid.id}: {data.concept_learned} ({data.years_compressed} years)")

    return event


@router.get(
    "/achievements/revealed",
    response_model=RevealedAchievementsResponse,
    summary="Get all revealed achievements",
    description="Retrieve all future slips that have been accidentally revealed."
)
async def get_revealed_achievements(
    kid: Child = Depends(get_current_kid),
    db: Session = Depends(get_db)
) -> RevealedAchievementsResponse:
    """
    Get all future slips that have been revealed.

    Returns:
        All revealed achievements/future slips
    """
    future_identity = db.query(FutureIdentity).filter(
        FutureIdentity.child_id == kid.id
    ).first()

    if not future_identity:
        raise NotFoundError("Future identity not found. Please set up your future profile first.")

    # Get all future slips
    slips = db.query(FutureSlip).filter(
        FutureSlip.future_identity_id == future_identity.id
    ).order_by(desc(FutureSlip.revealed_at)).all()

    achievements = [
        RevealedAchievementResponse(
            id=slip.id,
            type=slip.slip_type,
            content=slip.content,
            revealed_at=slip.revealed_at,
            supposed_year=slip.supposed_year,
            context=slip.context
        )
        for slip in slips
    ]

    return RevealedAchievementsResponse(achievements=achievements)


@router.post(
    "/timeline/recalculate",
    response_model=TimelineRecalculateResponse,
    summary="Recalculate timeline metrics",
    description="Manually trigger recalculation of user's timeline based on conversation history."
)
async def recalculate_timeline(
    data: TimelineRecalculateRequest,
    kid: Child = Depends(get_current_kid),
    db: Session = Depends(get_db)
) -> TimelineRecalculateResponse:
    """
    Recalculate user's timeline metrics.

    Analyzes all conversation history to:
    - Identify complex concepts discussed
    - Calculate cumulative timeline compression
    - Update thinking age
    - Determine trajectory

    Returns:
        Updated timeline metrics
    """
    future_identity = db.query(FutureIdentity).filter(
        FutureIdentity.child_id == kid.id
    ).first()

    if not future_identity:
        raise NotFoundError("Future identity not found. Please set up your future profile first.")

    # Recalculate timeline
    service = FutureSelfService()
    result = service.recalculate_timeline(future_identity, db)

    db.commit()
    db.refresh(future_identity)

    logger.info(f"Recalculated timeline for child {kid.id}: {result}")

    return TimelineRecalculateResponse(**result)

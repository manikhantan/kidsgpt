"""
Parent API endpoints.

Handles child management, content rules, monitoring features, and parent chat.
"""
from datetime import datetime
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.api.deps import get_db, get_current_parent, verify_parent_owns_child
from app.models import Parent, Child, ContentRule, ParentChatSession, ParentMessage, MessageRole
from app.schemas.child import ChildCreate, ChildUpdate, ChildResponse
from app.schemas.content_rule import ContentRuleUpdate, ContentRuleResponse
from app.schemas.parent_chat import (
    ParentChatMessageRequest,
    ParentChatResponse,
    ParentMessageResponse,
    ParentChatSessionSummary,
    PaginatedParentChatSessions,
    FullParentChatSession,
    CreateParentChatSessionResponse,
)
from app.core.security import hash_password
from app.core.exceptions import NotFoundError, ConflictError
from app.services.ai_service import get_ai_response, AIService, generate_session_title
from app.services.insights_service import (
    get_child_insights_dashboard,
    process_existing_messages,
)
from app.schemas.insights import ChildInsightsDashboard

router = APIRouter(prefix="/parent", tags=["parent"])


@router.post(
    "/children",
    response_model=ChildResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a child account",
    description="Create a new child account under the authenticated parent."
)
def create_child(
    data: ChildCreate,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db)
) -> ChildResponse:
    """
    Create a new child account.

    Creates a child with password, and name linked to the parent.
    """
    # Check if email already exists
    existing_child = db.query(Child).filter(Child.email == data.email).first()
    if existing_child:
        raise ConflictError("Email already exists")

    # Create child with hashed password
    new_child = Child(
        parent_id=parent.id,
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name
    )
    db.add(new_child)
    db.commit()
    db.refresh(new_child)

    return new_child


@router.get(
    "/children",
    response_model=List[ChildResponse],
    summary="List all children",
    description="Get a list of all children under the authenticated parent."
)
def list_children(
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db)
) -> List[ChildResponse]:
    """
    Get all children for the current parent.

    Returns a list of all child accounts created by this parent.
    """
    children = db.query(Child).filter(Child.parent_id == parent.id).all()
    return children


@router.put(
    "/children/{child_id}",
    response_model=ChildResponse,
    summary="Update child information",
    description="Update a child's name or password."
)
def update_child(
    child_id: UUID,
    data: ChildUpdate,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db)
) -> ChildResponse:
    """
    Update child account information.

    Parent can update the child's name or password.
    """
    # Verify parent owns this child
    child = verify_parent_owns_child(parent, child_id, db)

    # Update fields if provided
    if data.name is not None:
        child.name = data.name

    if data.password is not None:
        child.password_hash = hash_password(data.password)

    db.commit()
    db.refresh(child)

    return child


@router.delete(
    "/children/{child_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete child account",
    description="Delete a child account and all associated data."
)
def delete_child(
    child_id: UUID,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a child account.

    Removes the child and all their chat history (cascade delete).
    """
    # Verify parent owns this child
    child = verify_parent_owns_child(parent, child_id, db)

    db.delete(child)
    db.commit()


@router.get(
    "/content-rules",
    response_model=ContentRuleResponse,
    summary="Get content rules",
    description="Get the current content filtering rules."
)
def get_content_rules(
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db)
) -> ContentRuleResponse:
    """
    Get current content rules.

    Returns the parent's content filtering configuration.
    """
    rules = db.query(ContentRule).filter(
        ContentRule.parent_id == parent.id
    ).first()

    if not rules:
        raise NotFoundError("Content rules")

    return rules


@router.put(
    "/content-rules",
    response_model=ContentRuleResponse,
    summary="Update content rules",
    description="Update content filtering rules (allowlist or blocklist mode)."
)
def update_content_rules(
    data: ContentRuleUpdate,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db)
) -> ContentRuleResponse:
    """
    Update content filtering rules.

    Set the filtering mode (allowlist/blocklist) and topics/keywords.
    """
    rules = db.query(ContentRule).filter(
        ContentRule.parent_id == parent.id
    ).first()

    if not rules:
        raise NotFoundError("Content rules")

    # Update all fields
    rules.mode = data.mode
    rules.topics = data.topics
    rules.keywords = data.keywords

    db.commit()
    db.refresh(rules)

    return rules


# Parent Insights Dashboard Endpoints

@router.get(
    "/insights/{child_id}",
    response_model=ChildInsightsDashboard,
    summary="Get child insights dashboard",
    description="Get learning insights and analytics for a specific child without accessing actual conversations."
)
def get_child_insights(
    child_id: UUID,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db)
) -> ChildInsightsDashboard:
    """
    Get insights dashboard for a child.

    Returns aggregated insights including:
    - Top 5 topics of interest with time spent
    - Learning metrics (why/how questions vs answer-seeking)
    - Learning streak
    - Weekly highlights with suggestions

    This endpoint provides insights without exposing actual conversation content.
    """
    # Verify parent owns this child
    child = verify_parent_owns_child(parent, child_id, db)

    # Process any unprocessed messages first
    process_existing_messages(db, child.id)

    # Get the insights dashboard
    return get_child_insights_dashboard(db, child)


@router.post(
    "/insights/{child_id}/refresh",
    response_model=dict,
    summary="Refresh child insights",
    description="Process any new messages and regenerate insights for a child."
)
def refresh_child_insights(
    child_id: UUID,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db)
) -> dict:
    """
    Refresh insights by processing new messages.

    This endpoint processes any messages that haven't been analyzed yet
    and updates the aggregated insights.

    Returns:
        Count of newly processed messages
    """
    # Verify parent owns this child
    child = verify_parent_owns_child(parent, child_id, db)

    # Process unprocessed messages
    processed_count = process_existing_messages(db, child.id)

    return {
        "message": f"Successfully processed {processed_count} new messages",
        "processed_count": processed_count
    }


# Parent Chat Endpoints

@router.post(
    "/chat",
    response_model=ParentChatResponse,
    summary="Send a chat message",
    description="Send a message to the AI as a parent (no content filtering)."
)
def send_parent_chat_message(
    data: ParentChatMessageRequest,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db)
) -> ParentChatResponse:
    """
    Send a chat message to the AI as a parent.

    This endpoint:
    1. Validates the parent's JWT token
    2. Gets or creates chat session (uses provided sessionId or creates new)
    3. Sends message to AI (no content filtering for parents)
    4. Saves both messages and returns response
    5. Generates AI title after first message

    Returns:
        ParentChatResponse with user message, AI response, sessionId, and sessionTitle
    """
    # Get or create chat session
    if data.session_id:
        # Verify session belongs to this parent
        current_session = db.query(ParentChatSession).filter(
            ParentChatSession.id == data.session_id,
            ParentChatSession.parent_id == parent.id
        ).first()
        if not current_session:
            raise NotFoundError("Chat session not found or doesn't belong to you")
    else:
        # Create a new session
        current_session = ParentChatSession(
            parent_id=parent.id,
            title="New Chat",
            last_message_at=datetime.utcnow(),
            message_count=0
        )
        db.add(current_session)
        db.commit()
        db.refresh(current_session)

    # Save user message (no content filtering for parents)
    user_message = ParentMessage(
        session_id=current_session.id,
        role=MessageRole.USER,
        content=data.message
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # Get conversation history for context
    session_messages = db.query(ParentMessage).filter(
        ParentMessage.session_id == current_session.id
    ).order_by(ParentMessage.created_at.asc()).all()

    # Format history for AI (exclude the current message we just added)
    conversation_history = _format_parent_history(session_messages[:-1])

    # Get AI response
    ai_response_text = get_ai_response(data.message, conversation_history)

    # Save AI response
    assistant_message = ParentMessage(
        session_id=current_session.id,
        role=MessageRole.ASSISTANT,
        content=ai_response_text
    )
    db.add(assistant_message)

    # Update session metadata
    current_session.last_message_at = datetime.utcnow()
    current_session.message_count += 2  # Both user and assistant messages

    # Generate title after first user message if still default
    session_title = current_session.title
    user_messages_in_session = [
        msg.content for msg in session_messages if msg.role == MessageRole.USER
    ]

    # Generate title after first user message if still default
    if len(user_messages_in_session) == 1:
        # Generate AI title
        new_title = generate_session_title(user_messages_in_session)
        current_session.title = new_title
        session_title = new_title

    db.commit()
    db.refresh(assistant_message)

    return ParentChatResponse(
        user_message=ParentMessageResponse.model_validate(user_message),
        assistant_message=ParentMessageResponse.model_validate(assistant_message),
        session_id=current_session.id,
        session_title=session_title
    )


def _format_parent_history(messages: List[ParentMessage]) -> list:
    """
    Format parent messages into conversation history for AI.

    Args:
        messages: List of ParentMessage objects

    Returns:
        List of message dicts suitable for AI service
    """
    history = []
    for msg in messages:
        history.append({
            "role": msg.role.value,
            "content": msg.content
        })
    return history


@router.get(
    "/chat-sessions/recent",
    response_model=list[ParentChatSessionSummary],
    summary="Get recent chat sessions",
    description="Get the most recent chat sessions for the authenticated parent."
)
def get_recent_parent_chat_sessions(
    limit: int = Query(default=20, ge=1, le=100, description="Number of recent sessions to return"),
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db)
) -> list[ParentChatSessionSummary]:
    """
    Get recent chat sessions for the authenticated parent.

    Returns sessions ordered by lastMessageAt descending.
    """
    sessions = db.query(ParentChatSession).filter(
        ParentChatSession.parent_id == parent.id
    ).order_by(desc(ParentChatSession.last_message_at)).limit(limit).all()

    summaries = []
    for session in sessions:
        # Get preview from first user message
        preview = None
        first_user_message = db.query(ParentMessage).filter(
            ParentMessage.session_id == session.id,
            ParentMessage.role == MessageRole.USER
        ).order_by(ParentMessage.created_at.asc()).first()

        if first_user_message:
            preview = first_user_message.content[:100] if len(first_user_message.content) > 100 else first_user_message.content

        # Handle case where last_message_at is None
        last_message_at = session.last_message_at or session.started_at

        summaries.append(
            ParentChatSessionSummary(
                id=session.id,
                title=session.title or "New Chat",
                started_at=session.started_at,
                last_message_at=last_message_at,
                message_count=session.message_count or 0,
                preview=preview
            )
        )

    return summaries


@router.get(
    "/chat-sessions",
    response_model=PaginatedParentChatSessions,
    summary="Get paginated chat sessions",
    description="Get paginated list of all chat sessions for the authenticated parent."
)
def get_paginated_parent_chat_sessions(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=15, ge=1, le=50, description="Number of sessions per page"),
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db)
) -> PaginatedParentChatSessions:
    """
    Get paginated list of all chat sessions for the authenticated parent.

    Returns sessions ordered by lastMessageAt descending with pagination info.
    """
    # Get total count
    total = db.query(ParentChatSession).filter(
        ParentChatSession.parent_id == parent.id
    ).count()

    # Calculate offset
    offset = (page - 1) * page_size

    # Get sessions for current page
    sessions = db.query(ParentChatSession).filter(
        ParentChatSession.parent_id == parent.id
    ).order_by(desc(ParentChatSession.last_message_at)).offset(offset).limit(page_size).all()

    summaries = []
    for session in sessions:
        # Get preview from first user message
        preview = None
        first_user_message = db.query(ParentMessage).filter(
            ParentMessage.session_id == session.id,
            ParentMessage.role == MessageRole.USER
        ).order_by(ParentMessage.created_at.asc()).first()

        if first_user_message:
            preview = first_user_message.content[:100] if len(first_user_message.content) > 100 else first_user_message.content

        # Handle case where last_message_at is None
        last_message_at = session.last_message_at or session.started_at

        summaries.append(
            ParentChatSessionSummary(
                id=session.id,
                title=session.title or "New Chat",
                started_at=session.started_at,
                last_message_at=last_message_at,
                message_count=session.message_count or 0,
                preview=preview
            )
        )

    has_more = offset + page_size < total

    return PaginatedParentChatSessions(
        sessions=summaries,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.get(
    "/chat-sessions/{session_id}",
    response_model=FullParentChatSession,
    summary="Get full chat session",
    description="Get a full chat session with all messages."
)
def get_parent_chat_session_by_id(
    session_id: UUID,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db)
) -> FullParentChatSession:
    """
    Get a full chat session with all messages.

    Verifies that the session belongs to the authenticated parent.
    """
    session = db.query(ParentChatSession).filter(
        ParentChatSession.id == session_id,
        ParentChatSession.parent_id == parent.id
    ).first()

    if not session:
        raise NotFoundError("Chat session not found or doesn't belong to you")

    # Get all messages
    messages = [
        ParentMessageResponse.model_validate(msg)
        for msg in session.messages
    ]

    return FullParentChatSession(
        id=session.id,
        parent_id=session.parent_id,
        title=session.title,
        started_at=session.started_at,
        ended_at=session.ended_at,
        messages=messages,
        last_message_at=session.last_message_at,
        message_count=session.message_count
    )


@router.post(
    "/chat-sessions",
    response_model=CreateParentChatSessionResponse,
    summary="Create new chat session",
    description="Create a new empty chat session for the authenticated parent."
)
def create_parent_chat_session(
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db)
) -> CreateParentChatSessionResponse:
    """
    Create a new empty chat session for the authenticated parent.

    Returns the newly created session with a default title.
    """
    new_session = ParentChatSession(
        parent_id=parent.id,
        title="New Chat",
        last_message_at=datetime.utcnow(),
        message_count=0
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return CreateParentChatSessionResponse(
        id=new_session.id,
        parent_id=new_session.parent_id,
        title=new_session.title,
        started_at=new_session.started_at,
        messages=[]
    )

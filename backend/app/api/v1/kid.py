"""
Kid API endpoints.

Handles chat functionality with content filtering and AI integration.
"""
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.api.deps import get_db, get_current_kid
from app.models import Child, ContentRule, ChatSession, Message, MessageRole
from app.schemas.message import (
    ChatMessageRequest,
    ChatResponse,
    MessageResponse,
    ChatHistoryResponse,
    ChatSessionResponse,
    ChatSessionSummary,
    PaginatedChatSessions,
    FullChatSession,
    CreateChatSessionResponse,
)
from app.services.content_filter import filter_message
from app.services.ai_service import get_ai_response, AIService, generate_session_title
from app.core.exceptions import NotFoundError, AuthorizationError

router = APIRouter(prefix="/kid", tags=["kid"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a chat message",
    description="Send a message to the AI (subject to content filtering)."
)
def send_chat_message(
    data: ChatMessageRequest,
    kid: Child = Depends(get_current_kid),
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Send a chat message to the AI.

    This endpoint:
    1. Validates the kid's JWT token
    2. Gets or creates chat session (uses provided sessionId or creates new)
    3. Gets parent's content rules
    4. Filters the message against content rules
    5. If blocked: saves blocked message and returns error
    6. If allowed: sends to AI, saves both messages, returns response
    7. Generates AI title after 2-3 messages

    Returns:
        ChatResponse with user message, AI response, sessionId, and sessionTitle
    """
    # Get or create chat session
    if data.session_id:
        # Verify session belongs to this kid
        current_session = db.query(ChatSession).filter(
            ChatSession.id == data.session_id,
            ChatSession.child_id == kid.id
        ).first()
        if not current_session:
            raise NotFoundError("Chat session not found or doesn't belong to you")
    else:
        # Create a new session
        current_session = ChatSession(
            child_id=kid.id,
            title="New Chat",
            last_message_at=datetime.utcnow(),
            message_count=0
        )
        db.add(current_session)
        db.commit()
        db.refresh(current_session)

    # Get parent's content rules
    content_rules = db.query(ContentRule).filter(
        ContentRule.parent_id == kid.parent_id
    ).first()

    if not content_rules:
        # This shouldn't happen as rules are created on parent registration
        raise NotFoundError("Content rules not configured")

    # Filter the message against parent's rules
    is_allowed, block_reason = filter_message(data.message, content_rules)

    if not is_allowed:
        # Message blocked - save it and return error
        blocked_message = Message(
            session_id=current_session.id,
            role=MessageRole.USER,
            content=data.message,
            blocked=True,
            block_reason=block_reason
        )
        db.add(blocked_message)

        # Update session metadata
        current_session.last_message_at = datetime.utcnow()
        current_session.message_count += 1

        db.commit()
        db.refresh(blocked_message)

        return ChatResponse(
            user_message=MessageResponse.model_validate(blocked_message),
            assistant_message=None,
            was_blocked=True,
            block_reason=block_reason,
            session_id=current_session.id,
            session_title=current_session.title
        )

    # Message allowed - save user message
    user_message = Message(
        session_id=current_session.id,
        role=MessageRole.USER,
        content=data.message,
        blocked=False
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # Get conversation history for context
    session_messages = db.query(Message).filter(
        Message.session_id == current_session.id,
        Message.blocked == False
    ).order_by(Message.created_at.asc()).all()

    # Format history for AI (exclude the current message we just added)
    conversation_history = AIService.format_history_from_messages(
        session_messages[:-1]  # Exclude current message as it will be added by AI service
    )

    # Get AI response
    ai_response_text = get_ai_response(data.message, conversation_history)

    # Save AI response
    assistant_message = Message(
        session_id=current_session.id,
        role=MessageRole.ASSISTANT,
        content=ai_response_text,
        blocked=False
    )
    db.add(assistant_message)

    # Update session metadata
    current_session.last_message_at = datetime.utcnow()
    current_session.message_count += 2  # Both user and assistant messages

    # Generate title after 2-3 user messages if still default
    session_title = current_session.title
    user_messages_in_session = [
        msg.content for msg in session_messages if msg.role == MessageRole.USER
    ]
    user_messages_in_session.append(data.message)  # Include current message

    if (
        len(user_messages_in_session) >= 2
        and (current_session.title == "New Chat" or current_session.title is None)
    ):
        # Generate AI title
        new_title = generate_session_title(user_messages_in_session)
        current_session.title = new_title
        session_title = new_title

    db.commit()
    db.refresh(assistant_message)

    return ChatResponse(
        user_message=MessageResponse.model_validate(user_message),
        assistant_message=MessageResponse.model_validate(assistant_message),
        was_blocked=False,
        block_reason=None,
        session_id=current_session.id,
        session_title=session_title
    )


@router.get(
    "/chat-history",
    response_model=ChatHistoryResponse,
    summary="Get own chat history",
    description="Get the kid's own chat history."
)
def get_own_chat_history(
    kid: Child = Depends(get_current_kid),
    db: Session = Depends(get_db)
) -> ChatHistoryResponse:
    """
    Get the kid's own chat history.

    Returns all chat sessions and messages (excluding blocked messages
    from the kid's view for better experience).
    """
    # Get all sessions
    sessions = db.query(ChatSession).filter(
        ChatSession.child_id == kid.id
    ).order_by(ChatSession.started_at.desc()).all()

    # Build response (exclude blocked messages from kid's view)
    session_responses = []
    total_messages = 0

    for session in sessions:
        # Filter out blocked messages for kid's view
        messages = [
            MessageResponse.model_validate(msg)
            for msg in session.messages
            if not msg.blocked
        ]
        total_messages += len(messages)

        session_responses.append(
            ChatSessionResponse(
                id=session.id,
                child_id=session.child_id,
                started_at=session.started_at,
                ended_at=session.ended_at,
                messages=messages
            )
        )

    return ChatHistoryResponse(
        sessions=session_responses,
        total_sessions=len(sessions),
        total_messages=total_messages
    )


@router.get(
    "/current-session",
    response_model=ChatSessionResponse,
    summary="Get current chat session",
    description="Get or create the current chat session."
)
def get_current_session(
    kid: Child = Depends(get_current_kid),
    db: Session = Depends(get_db)
) -> ChatSessionResponse:
    """
    Get or create the current chat session.

    Returns the most recent open session or creates a new one.
    """
    session = _get_or_create_session(kid.id, db)

    # Get messages for this session (excluding blocked for kid's view)
    messages = [
        MessageResponse.model_validate(msg)
        for msg in session.messages
        if not msg.blocked
    ]

    return ChatSessionResponse(
        id=session.id,
        child_id=session.child_id,
        started_at=session.started_at,
        ended_at=session.ended_at,
        messages=messages
    )


def _get_or_create_session(child_id, db: Session) -> ChatSession:
    """
    Get the current open session or create a new one.

    Args:
        child_id: UUID of the child
        db: Database session

    Returns:
        ChatSession instance
    """
    # Look for an open session (no ended_at)
    open_session = db.query(ChatSession).filter(
        ChatSession.child_id == child_id,
        ChatSession.ended_at.is_(None)
    ).first()

    if open_session:
        return open_session

    # Create new session
    new_session = ChatSession(child_id=child_id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return new_session


# Chat Sessions Endpoints

@router.get(
    "/chat-sessions/recent",
    response_model=list[ChatSessionSummary],
    summary="Get recent chat sessions",
    description="Get the most recent chat sessions for the authenticated kid."
)
def get_recent_chat_sessions(
    limit: int = Query(default=20, ge=1, le=100, description="Number of recent sessions to return"),
    kid: Child = Depends(get_current_kid),
    db: Session = Depends(get_db)
) -> list[ChatSessionSummary]:
    """
    Get recent chat sessions for the authenticated kid.

    Returns sessions ordered by lastMessageAt descending.
    """
    sessions = db.query(ChatSession).filter(
        ChatSession.child_id == kid.id
    ).order_by(desc(ChatSession.last_message_at)).limit(limit).all()

    summaries = []
    for session in sessions:
        # Get preview from first user message
        preview = None
        first_user_message = db.query(Message).filter(
            Message.session_id == session.id,
            Message.role == MessageRole.USER,
            Message.blocked == False
        ).order_by(Message.created_at.asc()).first()

        if first_user_message:
            preview = first_user_message.content[:100] if len(first_user_message.content) > 100 else first_user_message.content

        # Handle case where last_message_at is None
        last_message_at = session.last_message_at or session.started_at

        summaries.append(
            ChatSessionSummary(
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
    response_model=PaginatedChatSessions,
    summary="Get paginated chat sessions",
    description="Get paginated list of all chat sessions for the authenticated kid."
)
def get_paginated_chat_sessions(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=15, ge=1, le=50, description="Number of sessions per page"),
    kid: Child = Depends(get_current_kid),
    db: Session = Depends(get_db)
) -> PaginatedChatSessions:
    """
    Get paginated list of all chat sessions for the authenticated kid.

    Returns sessions ordered by lastMessageAt descending with pagination info.
    """
    # Get total count
    total = db.query(ChatSession).filter(
        ChatSession.child_id == kid.id
    ).count()

    # Calculate offset
    offset = (page - 1) * page_size

    # Get sessions for current page
    sessions = db.query(ChatSession).filter(
        ChatSession.child_id == kid.id
    ).order_by(desc(ChatSession.last_message_at)).offset(offset).limit(page_size).all()

    summaries = []
    for session in sessions:
        # Get preview from first user message
        preview = None
        first_user_message = db.query(Message).filter(
            Message.session_id == session.id,
            Message.role == MessageRole.USER,
            Message.blocked == False
        ).order_by(Message.created_at.asc()).first()

        if first_user_message:
            preview = first_user_message.content[:100] if len(first_user_message.content) > 100 else first_user_message.content

        # Handle case where last_message_at is None
        last_message_at = session.last_message_at or session.started_at

        summaries.append(
            ChatSessionSummary(
                id=session.id,
                title=session.title or "New Chat",
                started_at=session.started_at,
                last_message_at=last_message_at,
                message_count=session.message_count or 0,
                preview=preview
            )
        )

    has_more = offset + page_size < total

    return PaginatedChatSessions(
        sessions=summaries,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.get(
    "/chat-sessions/{session_id}",
    response_model=FullChatSession,
    summary="Get full chat session",
    description="Get a full chat session with all messages."
)
def get_chat_session_by_id(
    session_id: UUID,
    kid: Child = Depends(get_current_kid),
    db: Session = Depends(get_db)
) -> FullChatSession:
    """
    Get a full chat session with all messages.

    Verifies that the session belongs to the authenticated kid.
    """
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.child_id == kid.id
    ).first()

    if not session:
        raise NotFoundError("Chat session not found or doesn't belong to you")

    # Get all messages (excluding blocked from kid's view)
    messages = [
        MessageResponse.model_validate(msg)
        for msg in session.messages
        if not msg.blocked
    ]

    return FullChatSession(
        id=session.id,
        child_id=session.child_id,
        title=session.title,
        started_at=session.started_at,
        ended_at=session.ended_at,
        messages=messages,
        last_message_at=session.last_message_at,
        message_count=session.message_count
    )


@router.post(
    "/chat-sessions",
    response_model=CreateChatSessionResponse,
    summary="Create new chat session",
    description="Create a new empty chat session for the authenticated kid."
)
def create_chat_session(
    kid: Child = Depends(get_current_kid),
    db: Session = Depends(get_db)
) -> CreateChatSessionResponse:
    """
    Create a new empty chat session for the authenticated kid.

    Returns the newly created session with a default title.
    """
    new_session = ChatSession(
        child_id=kid.id,
        title="New Chat",
        last_message_at=datetime.utcnow(),
        message_count=0
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return CreateChatSessionResponse(
        id=new_session.id,
        child_id=new_session.child_id,
        title=new_session.title,
        started_at=new_session.started_at,
        messages=[]
    )

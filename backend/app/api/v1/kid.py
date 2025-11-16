"""
Kid API endpoints.

Handles chat functionality with content filtering and AI integration.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_kid
from app.models import Child, ContentRule, ChatSession, Message, MessageRole
from app.schemas.message import (
    ChatMessageRequest,
    ChatResponse,
    MessageResponse,
    ChatHistoryResponse,
    ChatSessionResponse,
)
from app.services.content_filter import filter_message
from app.services.ai_service import get_ai_response, AIService
from app.core.exceptions import NotFoundError

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
    2. Gets parent's content rules
    3. Filters the message against content rules
    4. If blocked: saves blocked message and returns error
    5. If allowed: sends to AI, saves both messages, returns response

    Returns:
        ChatResponse with user message and AI response (if not blocked)
    """
    # Get or create current chat session
    current_session = _get_or_create_session(kid.id, db)

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
        db.commit()
        db.refresh(blocked_message)

        return ChatResponse(
            user_message=MessageResponse.model_validate(blocked_message),
            assistant_message=None,
            was_blocked=True,
            block_reason=block_reason
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
    db.commit()
    db.refresh(assistant_message)

    return ChatResponse(
        user_message=MessageResponse.model_validate(user_message),
        assistant_message=MessageResponse.model_validate(assistant_message),
        was_blocked=False,
        block_reason=None
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

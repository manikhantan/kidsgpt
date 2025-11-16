"""
Parent API endpoints.

Handles child management, content rules, and monitoring features.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.deps import get_db, get_current_parent, verify_parent_owns_child
from app.models import Parent, Child, ContentRule, ChatSession, Message
from app.schemas.child import ChildCreate, ChildUpdate, ChildResponse
from app.schemas.content_rule import ContentRuleUpdate, ContentRuleResponse
from app.schemas.parent import ParentAnalytics
from app.schemas.message import ChatHistoryResponse, ChatSessionResponse, MessageResponse
from app.core.security import hash_password
from app.core.exceptions import NotFoundError, ConflictError

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


@router.get(
    "/chat-history/{child_id}",
    response_model=ChatHistoryResponse,
    summary="Get child's chat history",
    description="View complete chat history for a specific child."
)
def get_child_chat_history(
    child_id: UUID,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db)
) -> ChatHistoryResponse:
    """
    Get complete chat history for a child.

    Returns all chat sessions and messages, including blocked attempts.
    """
    # Verify parent owns this child
    child = verify_parent_owns_child(parent, child_id, db)

    # Get all sessions with messages
    sessions = db.query(ChatSession).filter(
        ChatSession.child_id == child.id
    ).order_by(ChatSession.started_at.desc()).all()

    # Build response
    session_responses = []
    total_messages = 0

    for session in sessions:
        messages = [MessageResponse.model_validate(msg) for msg in session.messages]
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
    "/analytics/{child_id}",
    response_model=ParentAnalytics,
    summary="Get child analytics",
    description="Get usage analytics for a specific child."
)
def get_child_analytics(
    child_id: UUID,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db)
) -> ParentAnalytics:
    """
    Get analytics for a child.

    Returns statistics including total messages, blocked attempts, etc.
    """
    # Verify parent owns this child
    child = verify_parent_owns_child(parent, child_id, db)

    # Get total sessions
    total_sessions = db.query(func.count(ChatSession.id)).filter(
        ChatSession.child_id == child.id
    ).scalar()

    # Get total messages
    total_messages = db.query(func.count(Message.id)).join(ChatSession).filter(
        ChatSession.child_id == child.id
    ).scalar()

    # Get blocked messages
    blocked_messages = db.query(func.count(Message.id)).join(ChatSession).filter(
        ChatSession.child_id == child.id,
        Message.blocked == True
    ).scalar()

    # Get last activity
    last_message = db.query(Message.created_at).join(ChatSession).filter(
        ChatSession.child_id == child.id
    ).order_by(Message.created_at.desc()).first()

    last_activity = last_message[0] if last_message else None

    return ParentAnalytics(
        child_id=child.id,
        child_name=child.name,
        total_sessions=total_sessions or 0,
        total_messages=total_messages or 0,
        blocked_messages=blocked_messages or 0,
        last_activity=last_activity
    )

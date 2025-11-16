"""
API dependencies for authentication and database session management.

These dependencies are injected into route handlers via FastAPI's
dependency injection system.
"""
from typing import Generator, Tuple
from uuid import UUID
from fastapi import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.core.security import decode_token, verify_token_type
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.models import Parent, Child


# OAuth2 scheme for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/parent/login")


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency.

    Yields a database session and ensures it's properly closed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_token(
    token: str = Depends(oauth2_scheme)
) -> dict:
    """
    Validate JWT token and return payload.

    Args:
        token: JWT token from Authorization header

    Returns:
        Decoded token payload

    Raises:
        AuthenticationError: If token is invalid
    """
    payload = decode_token(token)

    if not payload:
        raise AuthenticationError("Invalid or expired token")

    if not verify_token_type(payload, "access"):
        raise AuthenticationError("Invalid token type")

    return payload


def get_current_parent(
    payload: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
) -> Parent:
    """
    Get current authenticated parent.

    Args:
        payload: Decoded JWT token payload
        db: Database session

    Returns:
        Parent model instance

    Raises:
        AuthenticationError: If token is invalid or user not found
        AuthorizationError: If user is not a parent
    """
    if payload.get("role") != "parent":
        raise AuthorizationError("Parent access required")

    parent_id = UUID(payload["sub"])
    parent = db.query(Parent).filter(Parent.id == parent_id).first()

    if not parent:
        raise AuthenticationError("Parent not found")

    return parent


def get_current_kid(
    payload: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
) -> Child:
    """
    Get current authenticated kid.

    Args:
        payload: Decoded JWT token payload
        db: Database session

    Returns:
        Child model instance

    Raises:
        AuthenticationError: If token is invalid or user not found
        AuthorizationError: If user is not a kid
    """
    if payload.get("role") != "kid":
        raise AuthorizationError("Kid access required")

    kid_id = UUID(payload["sub"])
    kid = db.query(Child).filter(Child.id == kid_id).first()

    if not kid:
        raise AuthenticationError("Kid not found")

    return kid


def get_current_user_with_role(
    payload: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
) -> Tuple[str, Parent | Child]:
    """
    Get current user regardless of role.

    Args:
        payload: Decoded JWT token payload
        db: Database session

    Returns:
        Tuple of (role, user_object)

    Raises:
        AuthenticationError: If user not found
    """
    role = payload.get("role")
    user_id = UUID(payload["sub"])

    if role == "parent":
        user = db.query(Parent).filter(Parent.id == user_id).first()
        if not user:
            raise AuthenticationError("Parent not found")
        return (role, user)
    elif role == "kid":
        user = db.query(Child).filter(Child.id == user_id).first()
        if not user:
            raise AuthenticationError("Kid not found")
        return (role, user)
    else:
        raise AuthenticationError("Invalid user role")


def verify_parent_owns_child(
    parent: Parent,
    child_id: UUID,
    db: Session
) -> Child:
    """
    Verify that a parent owns a specific child.

    Args:
        parent: Parent model instance
        child_id: UUID of the child to verify
        db: Database session

    Returns:
        Child model instance if owned by parent

    Raises:
        AuthorizationError: If parent does not own the child
    """
    child = db.query(Child).filter(
        Child.id == child_id,
        Child.parent_id == parent.id
    ).first()

    if not child:
        raise AuthorizationError("You do not have access to this child's data")

    return child

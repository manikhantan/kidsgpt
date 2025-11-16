"""
Authentication API endpoints.

Handles parent registration, parent/kid login, and token refresh.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.auth import (
    ParentRegister,
    ParentLogin,
    KidLogin,
    Token,
    TokenRefresh,
)
from app.schemas.parent import ParentResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/parent/register",
    response_model=ParentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new parent account",
    description="Create a new parent account with email, password, and name."
)
def register_parent(
    data: ParentRegister,
    db: Session = Depends(get_db)
) -> ParentResponse:
    """
    Register a new parent account.

    Creates a parent account and sets up default content rules.
    """
    parent = AuthService.register_parent(db, data)
    return parent


@router.post(
    "/parent/login",
    response_model=Token,
    summary="Parent login",
    description="Authenticate a parent and return JWT tokens."
)
def login_parent(
    data: ParentLogin,
    db: Session = Depends(get_db)
) -> Token:
    """
    Authenticate a parent and return access tokens.

    Returns access and refresh tokens for authenticated parent.
    """
    parent = AuthService.authenticate_parent(db, data.email, data.password)
    tokens = AuthService.create_tokens_for_parent(parent)
    return tokens


@router.post(
    "/kid/login",
    response_model=Token,
    summary="Kid login",
    description="Authenticate a kid and return JWT tokens."
)
def login_kid(
    data: KidLogin,
    db: Session = Depends(get_db)
) -> Token:
    """
    Authenticate a kid and return access tokens.

    Returns access and refresh tokens for authenticated kid.
    """
    child = AuthService.authenticate_kid(db, data.username, data.password)
    tokens = AuthService.create_tokens_for_kid(child)
    return tokens


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh JWT tokens",
    description="Get new access and refresh tokens using a valid refresh token."
)
def refresh_token(data: TokenRefresh) -> Token:
    """
    Refresh JWT tokens.

    Uses a valid refresh token to generate new access and refresh tokens.
    """
    tokens = AuthService.refresh_tokens(data.refresh_token)
    return tokens

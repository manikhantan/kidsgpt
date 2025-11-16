"""
Authentication service for user registration and login.
"""
from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from app.models import Parent, Child, ContentRule, ContentRuleMode
from app.schemas import ParentRegister, Token
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
)
from app.core.exceptions import AuthenticationError, ConflictError


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def register_parent(db: Session, data: ParentRegister) -> Parent:
        """
        Register a new parent account.

        Args:
            db: Database session
            data: Parent registration data

        Returns:
            Created parent object

        Raises:
            ConflictError: If email already exists
        """
        # Check if email already exists
        existing_parent = db.query(Parent).filter(
            Parent.email == data.email
        ).first()
        if existing_parent:
            raise ConflictError("Email already registered")

        # Create new parent with hashed password
        new_parent = Parent(
            email=data.email,
            password_hash=hash_password(data.password),
            name=data.name
        )
        db.add(new_parent)
        db.flush()

        # Create default content rules (blocklist mode with common restrictions)
        default_rules = ContentRule(
            parent_id=new_parent.id,
            mode=ContentRuleMode.BLOCKLIST,
            topics=[],
            keywords=["violence", "drugs", "weapons", "explicit", "adult"]
        )
        db.add(default_rules)

        db.commit()
        db.refresh(new_parent)

        return new_parent

    @staticmethod
    def authenticate_parent(
        db: Session,
        email: str,
        password: str
    ) -> Parent:
        """
        Authenticate a parent with email and password.

        Args:
            db: Database session
            email: Parent's email
            password: Plain text password

        Returns:
            Authenticated parent object

        Raises:
            AuthenticationError: If credentials are invalid
        """
        parent = db.query(Parent).filter(Parent.email == email).first()

        if not parent:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(password, parent.password_hash):
            raise AuthenticationError("Invalid email or password")

        return parent

    @staticmethod
    def authenticate_kid(
        db: Session,
        username: str,
        password: str
    ) -> Child:
        """
        Authenticate a kid with username and password.

        Args:
            db: Database session
            username: Kid's username
            password: Plain text password

        Returns:
            Authenticated child object

        Raises:
            AuthenticationError: If credentials are invalid
        """
        child = db.query(Child).filter(Child.username == username).first()

        if not child:
            raise AuthenticationError("Invalid username or password")

        if not verify_password(password, child.password_hash):
            raise AuthenticationError("Invalid username or password")

        return child

    @staticmethod
    def create_tokens_for_parent(parent: Parent) -> Token:
        """
        Create access and refresh tokens for a parent.

        Args:
            parent: Authenticated parent object

        Returns:
            Token object with access and refresh tokens
        """
        access_token = create_access_token(
            user_id=parent.id,
            role="parent",
            parent_id=parent.id
        )
        refresh_token = create_refresh_token(
            user_id=parent.id,
            role="parent",
            parent_id=parent.id
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )

    @staticmethod
    def create_tokens_for_kid(child: Child) -> Token:
        """
        Create access and refresh tokens for a kid.

        Args:
            child: Authenticated child object

        Returns:
            Token object with access and refresh tokens
        """
        access_token = create_access_token(
            user_id=child.id,
            role="kid",
            parent_id=child.parent_id
        )
        refresh_token = create_refresh_token(
            user_id=child.id,
            role="kid",
            parent_id=child.parent_id
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )

    @staticmethod
    def refresh_tokens(refresh_token_str: str) -> Token:
        """
        Refresh access token using a valid refresh token.

        Args:
            refresh_token_str: Refresh token string

        Returns:
            New Token object with fresh access and refresh tokens

        Raises:
            AuthenticationError: If refresh token is invalid
        """
        payload = decode_token(refresh_token_str)

        if not payload:
            raise AuthenticationError("Invalid refresh token")

        if not verify_token_type(payload, "refresh"):
            raise AuthenticationError("Invalid token type")

        user_id = UUID(payload["sub"])
        role = payload["role"]
        parent_id = UUID(payload["parent_id"])

        # Create new tokens
        access_token = create_access_token(
            user_id=user_id,
            role=role,
            parent_id=parent_id
        )
        new_refresh_token = create_refresh_token(
            user_id=user_id,
            role=role,
            parent_id=parent_id
        )

        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token
        )

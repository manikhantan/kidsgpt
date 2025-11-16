"""
Authentication schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


class ParentRegister(BaseModel):
    """Schema for parent registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)


class ParentLogin(BaseModel):
    """Schema for parent login."""
    email: EmailStr
    password: str


class KidLogin(BaseModel):
    """Schema for kid login."""
    username: str = Field(..., min_length=1, max_length=50)
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""
    sub: UUID  # User ID
    role: str  # "parent" or "kid"
    parent_id: UUID  # Parent ID (same as sub for parents)
    exp: int  # Expiration timestamp

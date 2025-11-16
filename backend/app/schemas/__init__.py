"""
Pydantic schemas package.

Exports all schemas for easy importing.
"""
from app.schemas.auth import (
    ParentRegister,
    ParentLogin,
    KidLogin,
    Token,
    TokenRefresh,
    TokenPayload,
)
from app.schemas.parent import (
    ParentCreate,
    ParentUpdate,
    ParentResponse,
    ParentAnalytics,
)
from app.schemas.child import (
    ChildCreate,
    ChildUpdate,
    ChildResponse,
    ChildProfile,
)
from app.schemas.content_rule import (
    ContentRuleCreate,
    ContentRuleUpdate,
    ContentRuleResponse,
)
from app.schemas.message import (
    ChatMessageRequest,
    MessageResponse,
    ChatResponse,
    ChatSessionResponse,
    ChatHistoryResponse,
)

__all__ = [
    # Auth
    "ParentRegister",
    "ParentLogin",
    "KidLogin",
    "Token",
    "TokenRefresh",
    "TokenPayload",
    # Parent
    "ParentCreate",
    "ParentUpdate",
    "ParentResponse",
    "ParentAnalytics",
    # Child
    "ChildCreate",
    "ChildUpdate",
    "ChildResponse",
    "ChildProfile",
    # Content Rule
    "ContentRuleCreate",
    "ContentRuleUpdate",
    "ContentRuleResponse",
    # Message
    "ChatMessageRequest",
    "MessageResponse",
    "ChatResponse",
    "ChatSessionResponse",
    "ChatHistoryResponse",
]

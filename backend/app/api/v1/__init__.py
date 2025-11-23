"""
API v1 package.

Contains all API route modules.
"""
from app.api.v1 import auth, parent, kid, future_self

__all__ = ["auth", "parent", "kid", "future_self"]

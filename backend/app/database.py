"""
Database connection and session management.

Provides SQLAlchemy engine and session factory for PostgreSQL database.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    echo=settings.DEBUG  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()


def get_db():
    """
    Dependency that provides database session.

    Yields a database session and ensures it's closed after use.
    Use this as a FastAPI dependency in route handlers.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

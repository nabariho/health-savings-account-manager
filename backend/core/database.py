"""
Database configuration and session management.

This module provides SQLAlchemy database configuration, session management,
and base model classes for the HSA application.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String, create_engine
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings


# Create database engine (using synchronous SQLAlchemy for simplicity)
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
    echo=settings.debug
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Base model class
Base = declarative_base()


class BaseModel(Base):
    """
    Base model class with common fields.
    
    Provides:
    - id: UUID primary key
    - created_at: Timestamp when record was created
    - updated_at: Timestamp when record was last updated
    """
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True) if not settings.database_url.startswith("sqlite") else String,
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
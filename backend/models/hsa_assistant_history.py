"""
HSA Assistant history database model.

This module defines the SQLAlchemy model for tracking HSA Assistant interactions
in the HSA knowledge base system, supporting user story requirements.
"""

from sqlalchemy import Column, String, Text, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from ..core.database import BaseModel


class HSAAssistantHistory(BaseModel):
    """
    HSA Assistant history tracking model.
    
    Tracks all question-answer interactions for analysis and improvement
    of the RAG system performance.
    """
    __tablename__ = "hsa_assistant_history"
    
    # Question details
    question = Column(
        Text,
        nullable=False,
        comment="The question that was asked"
    )
    
    # Answer details
    answer = Column(
        Text,
        nullable=False,
        comment="The generated answer"
    )
    
    # Quality metrics
    confidence_score = Column(
        Float,
        nullable=False,
        comment="Confidence score for the answer (0.0 to 1.0)"
    )
    
    citations_count = Column(
        Integer,
        default=0,
        comment="Number of citations included in the answer"
    )
    
    processing_time_ms = Column(
        Integer,
        comment="Time taken to process the question in milliseconds"
    )
    
    # Context and tracking
    application_id = Column(
        String(255),
        nullable=True,
        comment="Associated application ID if available"
    )
    
    context = Column(
        Text,
        nullable=True,
        comment="Optional context provided with the question"
    )
    
    # Source tracking
    source_documents = Column(
        Text,
        comment="JSON array of source document names used"
    )
    
    # User feedback (for future enhancement)
    user_rating = Column(
        Integer,
        nullable=True,
        comment="User rating of the answer quality (1-5)"
    )
    
    feedback_notes = Column(
        Text,
        nullable=True,
        comment="Optional user feedback notes"
    )
    
    def __repr__(self):
        """String representation of HSA Assistant history record."""
        return f"<HSAAssistantHistory(id={self.id}, confidence={self.confidence_score:.2f})>"
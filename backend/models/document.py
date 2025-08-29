"""
Document model for storing uploaded files and extracted data.

This module defines the SQLAlchemy model for documents uploaded during
the HSA onboarding process, including government IDs and employer documents.
"""

from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Index

from ..core.database import BaseModel


class Document(BaseModel):
    """
    Document model for file uploads and OCR data.
    
    Stores information about uploaded documents including metadata,
    processing status, and extracted data from OpenAI vision processing.
    
    Attributes:
        application_id: Reference to the associated application
        document_type: Type of document (government_id, employer_document)
        file_name: Original filename
        file_path: Storage path for the uploaded file
        content_type: MIME type of the file
        file_size: Size of the file in bytes
        processing_status: Current processing status
        extracted_data: JSON data extracted from the document
        processing_error: Error message if processing failed
        confidence_scores: Confidence scores for extracted fields
    """
    __tablename__ = "documents"
    
    # Foreign key to applications table
    application_id = Column(
        String,
        ForeignKey("applications.id"),
        nullable=False,
        index=True,
        comment="Associated application ID"
    )
    
    # Document metadata
    document_type = Column(
        String(20),
        nullable=False,
        comment="Type of document (government_id, employer_document)"
    )
    
    file_name = Column(
        String(255),
        nullable=False,
        comment="Original filename"
    )
    
    file_path = Column(
        String(500),
        nullable=False,
        comment="Storage path for the file"
    )
    
    content_type = Column(
        String(50),
        nullable=False,
        comment="MIME type of the file"
    )
    
    file_size = Column(
        Integer,
        nullable=False,
        comment="File size in bytes"
    )
    
    # Processing status and results
    processing_status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
        comment="Processing status (pending, processing, completed, failed)"
    )
    
    extracted_data = Column(
        JSON,
        nullable=True,
        comment="Extracted data from document processing"
    )
    
    processing_error = Column(
        Text,
        nullable=True,
        comment="Error message if processing failed"
    )
    
    confidence_scores = Column(
        JSON,
        nullable=True,
        comment="Confidence scores for extracted fields"
    )
    
    # Relationship to application
    application = relationship("Application", back_populates="documents")
    
    # Additional indexes for performance
    __table_args__ = (
        Index("idx_documents_application_type", "application_id", "document_type"),
        Index("idx_documents_status_created", "processing_status", "created_at"),
    )
    
    def __repr__(self) -> str:
        """String representation of the document."""
        return f"<Document(id={self.id}, type='{self.document_type}', status='{self.processing_status}')>"
    
    def to_dict(self) -> dict:
        """Convert document to dictionary representation."""
        return {
            "id": str(self.id),
            "application_id": str(self.application_id),
            "document_type": self.document_type,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "content_type": self.content_type,
            "file_size": self.file_size,
            "processing_status": self.processing_status,
            "extracted_data": self.extracted_data,
            "processing_error": self.processing_error,
            "confidence_scores": self.confidence_scores,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
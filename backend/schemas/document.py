"""
Document schemas for data validation and serialization.

This module defines Pydantic models for document-related data transfer objects (DTOs),
providing validation, serialization, and documentation for document processing APIs.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, validator


class DocumentType(str, Enum):
    """Document type enumeration."""
    GOVERNMENT_ID = "government_id"
    EMPLOYER_DOCUMENT = "employer_document"


class ProcessingStatus(str, Enum):
    """Document processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentUploadRequest(BaseModel):
    """Document upload request schema."""
    
    document_type: DocumentType = Field(
        ...,
        description="Type of document being uploaded"
    )
    
    application_id: str = Field(
        ...,
        description="Application ID this document belongs to"
    )


class GovernmentIdData(BaseModel):
    """Extracted government ID data schema."""
    
    document_type: str = Field(
        ...,
        description="Type of government ID (driver's license, passport, etc.)",
        example="driver's license"
    )
    
    id_number: str = Field(
        ...,
        description="ID number from the document",
        example="D1234567"
    )
    
    full_name: str = Field(
        ...,
        description="Full name as it appears on the ID",
        example="John Doe"
    )
    
    date_of_birth: date = Field(
        ...,
        description="Date of birth from the ID",
        example="1990-01-15"
    )
    
    address_street: Optional[str] = Field(
        None,
        description="Street address from the ID",
        example="123 Main Street"
    )
    
    address_city: Optional[str] = Field(
        None,
        description="City from the ID",
        example="Anytown"
    )
    
    address_state: Optional[str] = Field(
        None,
        description="State from the ID",
        example="CA"
    )
    
    address_zip: Optional[str] = Field(
        None,
        description="ZIP code from the ID",
        example="12345"
    )
    
    issue_date: Optional[date] = Field(
        None,
        description="Issue date of the ID"
    )
    
    expiry_date: Optional[date] = Field(
        None,
        description="Expiry date of the ID"
    )
    
    issuing_authority: Optional[str] = Field(
        None,
        description="Issuing authority",
        example="Department of Motor Vehicles"
    )


class EmployerDocumentData(BaseModel):
    """Extracted employer document data schema."""
    
    document_type: str = Field(
        ...,
        description="Type of employer document",
        example="pay stub"
    )
    
    employee_name: str = Field(
        ...,
        description="Employee name from the document",
        example="John Doe"
    )
    
    employer_name: str = Field(
        ...,
        description="Employer name from the document",
        example="Acme Corporation"
    )
    
    employer_address: Optional[str] = Field(
        None,
        description="Employer address if available"
    )
    
    document_date: Optional[date] = Field(
        None,
        description="Date on the document"
    )
    
    health_plan_type: Optional[str] = Field(
        None,
        description="Type of health plan mentioned"
    )


class DocumentProcessingResponse(BaseModel):
    """Document processing response schema."""
    
    id: str = Field(
        ...,
        description="Document unique identifier"
    )
    
    application_id: str = Field(
        ...,
        description="Associated application ID"
    )
    
    document_type: DocumentType = Field(
        ...,
        description="Type of document"
    )
    
    file_name: str = Field(
        ...,
        description="Original filename"
    )
    
    content_type: str = Field(
        ...,
        description="MIME type of the file"
    )
    
    file_size: int = Field(
        ...,
        description="File size in bytes"
    )
    
    processing_status: ProcessingStatus = Field(
        ...,
        description="Current processing status"
    )
    
    extracted_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Extracted data from the document"
    )
    
    processing_error: Optional[str] = Field(
        None,
        description="Error message if processing failed"
    )
    
    confidence_scores: Optional[Dict[str, float]] = Field(
        None,
        description="Confidence scores for extracted fields"
    )
    
    created_at: datetime = Field(
        ...,
        description="When the document was uploaded"
    )
    
    updated_at: datetime = Field(
        ...,
        description="When the document was last updated"
    )


class DocumentStatusResponse(BaseModel):
    """Document status response schema."""
    
    id: str = Field(
        ...,
        description="Document unique identifier"
    )
    
    processing_status: ProcessingStatus = Field(
        ...,
        description="Current processing status"
    )
    
    extracted_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Extracted data if processing completed"
    )
    
    processing_error: Optional[str] = Field(
        None,
        description="Error message if processing failed"
    )
    
    confidence_scores: Optional[Dict[str, float]] = Field(
        None,
        description="Confidence scores for extracted fields"
    )
    
    updated_at: datetime = Field(
        ...,
        description="When the document was last updated"
    )


class ValidationResult(BaseModel):
    """Validation result for comparing extracted data with application data."""
    
    field_name: str = Field(
        ...,
        description="Name of the field being validated"
    )
    
    application_value: Optional[str] = Field(
        None,
        description="Value from the application"
    )
    
    document_value: Optional[str] = Field(
        None,
        description="Value extracted from the document"
    )
    
    is_match: bool = Field(
        ...,
        description="Whether the values match"
    )
    
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for the match"
    )
    
    reason: Optional[str] = Field(
        None,
        description="Reason for the validation result"
    )


class DocumentValidationResponse(BaseModel):
    """Document validation response schema."""
    
    document_id: str = Field(
        ...,
        description="Document unique identifier"
    )
    
    application_id: str = Field(
        ...,
        description="Associated application ID"
    )
    
    overall_match_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall match score between document and application data"
    )
    
    validation_results: List[ValidationResult] = Field(
        ...,
        description="Individual field validation results"
    )
    
    recommendation: str = Field(
        ...,
        description="Recommendation based on validation (APPROVE, MANUAL_REVIEW, REJECT)"
    )
    
    created_at: datetime = Field(
        ...,
        description="When the validation was performed"
    )
"""
Decision engine schemas for HSA application processing.

This module defines Pydantic models for decision-related data transfer objects (DTOs),
providing validation, serialization, and documentation for decision engine APIs.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class DecisionType(str, Enum):
    """Decision outcome enumeration."""
    APPROVE = "approve"
    REJECT = "reject"
    MANUAL_REVIEW = "manual_review"


class ValidationType(str, Enum):
    """Validation type enumeration."""
    NAME_MATCH = "name_match"
    DOB_MATCH = "dob_match"
    ADDRESS_MATCH = "address_match"
    ID_EXPIRY = "id_expiry"
    DOCUMENT_QUALITY = "document_quality"
    EMPLOYER_MATCH = "employer_match"


class ValidationResult(BaseModel):
    """Individual validation result schema."""
    
    field_name: str = Field(
        ...,
        description="Name of the field being validated"
    )
    
    validation_type: ValidationType = Field(
        ...,
        description="Type of validation performed"
    )
    
    is_valid: bool = Field(
        ...,
        description="Whether the validation passed"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for this validation"
    )
    
    details: Optional[str] = Field(
        None,
        description="Additional details about the validation result"
    )
    
    application_value: Optional[str] = Field(
        None,
        description="Value from the application"
    )
    
    document_value: Optional[str] = Field(
        None,
        description="Value from the document"
    )


class DecisionRequest(BaseModel):
    """Decision evaluation request schema."""
    
    application_id: str = Field(
        ...,
        description="Application ID to evaluate"
    )


class ApplicationData(BaseModel):
    """Complete application data for decision making."""
    
    application_id: str = Field(..., description="Application unique identifier")
    full_name: str = Field(..., description="Applicant full name")
    date_of_birth: str = Field(..., description="Date of birth")
    address_street: str = Field(..., description="Street address")
    address_city: str = Field(..., description="City")
    address_state: str = Field(..., description="State")
    address_zip: str = Field(..., description="ZIP code")
    social_security_number: str = Field(..., description="Social security number")
    employer_name: str = Field(..., description="Employer name")
    
    # Extracted document data
    government_id_data: Optional[Dict[str, Any]] = Field(
        None, description="Extracted government ID data"
    )
    employer_document_data: Optional[Dict[str, Any]] = Field(
        None, description="Extracted employer document data"
    )


class DecisionResult(BaseModel):
    """Decision evaluation result schema."""
    
    application_id: str = Field(
        ...,
        description="Application ID that was evaluated"
    )
    
    decision: DecisionType = Field(
        ...,
        description="Final decision outcome"
    )
    
    risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall risk score (0 = low risk, 1 = high risk)"
    )
    
    reasoning: str = Field(
        ...,
        description="Human-readable explanation of the decision"
    )
    
    validation_results: List[ValidationResult] = Field(
        default_factory=list,
        description="Individual validation results"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the decision was made"
    )


class DecisionConfig(BaseModel):
    """Configuration for decision engine rules."""
    
    name_match_threshold: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score for name matching"
    )
    
    auto_approve_threshold: float = Field(
        0.1,
        ge=0.0,
        le=1.0,
        description="Maximum risk score for automatic approval"
    )
    
    manual_review_threshold: float = Field(
        0.3,
        ge=0.0,
        le=1.0,
        description="Risk score threshold for manual review"
    )
    
    expired_id_auto_reject: bool = Field(
        True,
        description="Automatically reject applications with expired IDs"
    )


class AuditEntry(BaseModel):
    """Audit trail entry for decision tracking."""
    
    application_id: str = Field(..., description="Application ID")
    decision: DecisionType = Field(..., description="Decision made")
    risk_score: float = Field(..., description="Risk score calculated")
    reasoning: str = Field(..., description="Decision reasoning")
    validation_results: List[ValidationResult] = Field(
        default_factory=list, description="Validation results"
    )
    application_snapshot: Dict[str, Any] = Field(
        default_factory=dict, description="Complete application data at time of decision"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the decision was made"
    )
    system_version: str = Field(..., description="System version that made the decision")


class AuditTrail(BaseModel):
    """Complete audit trail for an application."""
    
    application_id: str = Field(..., description="Application ID")
    entries: List[AuditEntry] = Field(
        default_factory=list, description="Audit entries in chronological order"
    )
    created_at: datetime = Field(..., description="First audit entry timestamp")
    updated_at: datetime = Field(..., description="Last audit entry timestamp")
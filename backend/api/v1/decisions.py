"""
Decision API endpoints for HSA application evaluation.

This module provides REST API endpoints for automated decision making,
application evaluation, and audit trail management.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.application import Application
from ...models.document import Document
from ...schemas.decision import (
    DecisionRequest, DecisionResult, ApplicationData, DecisionConfig,
    AuditTrail
)
from ...schemas.document import DocumentType, ProcessingStatus
from ...services.decision_engine import DecisionEngine, DecisionEngineError, AuditService

# Create router for decision endpoints
router = APIRouter(prefix="/decisions", tags=["decisions"])

# Initialize services
decision_engine = DecisionEngine()
audit_service = AuditService()


@router.post("/evaluate", response_model=DecisionResult)
async def evaluate_application(
    request: DecisionRequest,
    db: Session = Depends(get_db)
) -> DecisionResult:
    """
    Evaluate an HSA application for automated decision making.
    
    This endpoint performs comprehensive evaluation of an application including:
    - Government ID validation and expiry check
    - Data consistency verification between application and documents
    - Risk assessment and scoring
    - Automated decision based on business rules
    
    Business Rules:
    - Expired ID → Reject
    - Data mismatches → Manual Review
    - All valid criteria met → Approve
    
    Args:
        request: Decision evaluation request
        db: Database session dependency
        
    Returns:
        DecisionResult: Evaluation outcome with detailed reasoning
        
    Raises:
        HTTPException: If application not found or evaluation fails
    """
    
    # Get application data
    application = db.query(Application).filter(
        Application.id == request.application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Get associated documents
    documents = db.query(Document).filter(
        Document.application_id == request.application_id,
        Document.processing_status == ProcessingStatus.COMPLETED.value
    ).all()
    
    # Extract document data
    government_id_data = None
    employer_document_data = None
    
    for doc in documents:
        if doc.document_type == DocumentType.GOVERNMENT_ID.value and doc.extracted_data:
            government_id_data = doc.extracted_data
        elif doc.document_type == DocumentType.EMPLOYER_DOCUMENT.value and doc.extracted_data:
            employer_document_data = doc.extracted_data
    
    # Prepare application data for evaluation
    application_data = ApplicationData(
        application_id=request.application_id,
        full_name=application.full_name,
        date_of_birth=str(application.date_of_birth),
        address_street=application.address_street,
        address_city=application.address_city,
        address_state=application.address_state,
        address_zip=application.address_zip,
        social_security_number=application.social_security_number,
        employer_name=application.employer_name,
        government_id_data=government_id_data,
        employer_document_data=employer_document_data
    )
    
    try:
        # Evaluate application
        decision_result = await decision_engine.evaluate_application(application_data)
        
        # Log to audit trail
        await audit_service.log_decision(decision_result, application_data)
        
        return decision_result
        
    except DecisionEngineError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Decision evaluation failed: {str(e)}"
        )


@router.get("/{application_id}", response_model=DecisionResult)
async def get_application_decision(
    application_id: str,
    db: Session = Depends(get_db)
) -> DecisionResult:
    """
    Get the current decision status for an application.
    
    Args:
        application_id: Application unique identifier
        db: Database session dependency
        
    Returns:
        DecisionResult: Current decision information
        
    Raises:
        HTTPException: If application not found or no decision available
    """
    # In a real implementation, this would query a decisions table
    # For now, return a not found response
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Decision not found. Use POST /evaluate to create a decision."
    )


@router.get("/audit/{application_id}", response_model=AuditTrail)
async def get_audit_trail(
    application_id: str,
    db: Session = Depends(get_db)
) -> AuditTrail:
    """
    Get detailed audit trail for an application's decision history.
    
    Args:
        application_id: Application unique identifier
        db: Database session dependency
        
    Returns:
        AuditTrail: Complete audit history with all decision events
        
    Raises:
        HTTPException: If application not found
    """
    # Verify application exists
    application = db.query(Application).filter(
        Application.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    try:
        audit_trail = await audit_service.get_audit_trail(application_id)
        return audit_trail
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit trail: {str(e)}"
        )


@router.get("/config", response_model=DecisionConfig)
async def get_decision_config() -> DecisionConfig:
    """
    Get current decision engine configuration.
    
    Returns:
        DecisionConfig: Current configuration parameters
    """
    return decision_engine.config


@router.post("/config", response_model=DecisionConfig)
async def update_decision_config(config: DecisionConfig) -> DecisionConfig:
    """
    Update decision engine configuration.
    
    Args:
        config: New configuration parameters
        
    Returns:
        DecisionConfig: Updated configuration
        
    Note:
        In production, this endpoint should be protected with admin authentication.
    """
    global decision_engine
    decision_engine = DecisionEngine(config)
    return config
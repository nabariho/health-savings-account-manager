"""
Document API endpoints for HSA onboarding.

This module provides REST API endpoints for managing document uploads,
processing, and validation during the HSA onboarding process.
"""

import os
import uuid
from typing import List
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ...core.database import get_db
from ...core.config import settings
from ...models.application import Application
from ...models.document import Document
from ...schemas.document import (
    DocumentType,
    DocumentUploadRequest,
    DocumentProcessingResponse,
    DocumentStatusResponse,
    DocumentValidationResponse,
    ValidationResult,
    ProcessingStatus
)
from ...services.document_processor import DocumentProcessor, DocumentProcessingError

# Create router for document endpoints
router = APIRouter(prefix="/documents", tags=["documents"])

# Initialize document processor
document_processor = DocumentProcessor()


@router.post("/upload", response_model=DocumentProcessingResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    application_id: str = Form(...),
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> DocumentProcessingResponse:
    """
    Upload and process a document for an HSA application.
    
    This endpoint handles file upload, storage, and initiates OCR processing
    using OpenAI GPT-4o vision capabilities.
    
    Args:
        application_id: Application ID this document belongs to
        document_type: Type of document (government_id or employer_document)
        file: Uploaded file (image format)
        db: Database session dependency
        
    Returns:
        DocumentProcessingResponse: Upload status and processing information
        
    Raises:
        HTTPException: If validation fails, file issues, or processing errors
    """
    
    # Validate application exists
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No filename provided"
        )
    
    # Check file type
    allowed_types = {
        "image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif",
        "application/pdf"
    }
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type: {file.content_type}. Supported types: {allowed_types}"
        )
    
    # Check file size
    file_content = await file.read()
    if len(file_content) > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.max_file_size} bytes"
        )
    
    try:
        # Create upload directory if it doesn't exist
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Create document record
        document = Document(
            application_id=application_id,
            document_type=document_type.value,
            file_name=file.filename,
            file_path=str(file_path),
            content_type=file.content_type,
            file_size=len(file_content),
            processing_status=ProcessingStatus.PROCESSING.value
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Process document asynchronously
        try:
            extracted_data, confidence_scores = await document_processor.process_document(
                file_content=file_content,
                document_type=document_type,
                file_name=file.filename
            )
            
            # Update document with extracted data
            document.extracted_data = extracted_data
            document.confidence_scores = confidence_scores
            document.processing_status = ProcessingStatus.COMPLETED.value
            document.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(document)
            
        except DocumentProcessingError as e:
            # Update document with error
            document.processing_status = ProcessingStatus.FAILED.value
            document.processing_error = str(e)
            document.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(document)
        
        # Return response
        return DocumentProcessingResponse(
            id=str(document.id),
            application_id=str(document.application_id),
            document_type=DocumentType(document.document_type),
            file_name=document.file_name,
            content_type=document.content_type,
            file_size=document.file_size,
            processing_status=ProcessingStatus(document.processing_status),
            extracted_data=document.extracted_data,
            processing_error=document.processing_error,
            confidence_scores=document.confidence_scores,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
        
    except Exception as e:
        # Clean up file if database operation fails
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        
        # Rollback database changes
        db.rollback()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document upload: {str(e)}"
        )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(
    document_id: str,
    db: Session = Depends(get_db)
) -> DocumentStatusResponse:
    """
    Get processing status of a document.
    
    Args:
        document_id: Document unique identifier
        db: Database session dependency
        
    Returns:
        DocumentStatusResponse: Processing status and results
        
    Raises:
        HTTPException: If document not found
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentStatusResponse(
        id=str(document.id),
        processing_status=ProcessingStatus(document.processing_status),
        extracted_data=document.extracted_data,
        processing_error=document.processing_error,
        confidence_scores=document.confidence_scores,
        updated_at=document.updated_at
    )


@router.get("/application/{application_id}", response_model=List[DocumentProcessingResponse])
def list_application_documents(
    application_id: str,
    db: Session = Depends(get_db)
) -> List[DocumentProcessingResponse]:
    """
    List all documents for an application.
    
    Args:
        application_id: Application unique identifier
        db: Database session dependency
        
    Returns:
        List[DocumentProcessingResponse]: List of documents for the application
        
    Raises:
        HTTPException: If application not found
    """
    # Verify application exists
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Get documents
    documents = db.query(Document).filter(
        Document.application_id == application_id
    ).order_by(Document.created_at.desc()).all()
    
    return [
        DocumentProcessingResponse(
            id=str(doc.id),
            application_id=str(doc.application_id),
            document_type=DocumentType(doc.document_type),
            file_name=doc.file_name,
            content_type=doc.content_type,
            file_size=doc.file_size,
            processing_status=ProcessingStatus(doc.processing_status),
            extracted_data=doc.extracted_data,
            processing_error=doc.processing_error,
            confidence_scores=doc.confidence_scores,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )
        for doc in documents
    ]


@router.post("/{document_id}/validate", response_model=DocumentValidationResponse)
def validate_document(
    document_id: str,
    db: Session = Depends(get_db)
) -> DocumentValidationResponse:
    """
    Validate extracted document data against application information.
    
    Compares the data extracted from the document with the personal
    information provided in the application to detect discrepancies.
    
    Args:
        document_id: Document unique identifier
        db: Database session dependency
        
    Returns:
        DocumentValidationResponse: Validation results and recommendations
        
    Raises:
        HTTPException: If document not found or not processed
    """
    # Get document with application data
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.processing_status != ProcessingStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Document processing not completed"
        )
    
    if not document.extracted_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No extracted data available for validation"
        )
    
    # Get application data
    application = db.query(Application).filter(Application.id == document.application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated application not found"
        )
    
    # Prepare application data for validation
    application_data = {
        "full_name": application.full_name,
        "date_of_birth": str(application.date_of_birth),
        "address_street": application.address_street,
        "address_city": application.address_city,
        "address_state": application.address_state,
        "address_zip": application.address_zip,
        "employer_name": application.employer_name
    }
    
    # Perform validation
    validation_results, overall_score = document_processor.validate_against_application(
        extracted_data=document.extracted_data,
        application_data=application_data,
        document_type=DocumentType(document.document_type)
    )
    
    # Determine recommendation
    if overall_score >= 0.9:
        recommendation = "APPROVE"
    elif overall_score >= 0.7:
        recommendation = "MANUAL_REVIEW"
    else:
        recommendation = "REJECT"
    
    return DocumentValidationResponse(
        document_id=str(document.id),
        application_id=str(document.application_id),
        overall_match_score=overall_score,
        validation_results=validation_results,
        recommendation=recommendation,
        created_at=datetime.utcnow()
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a document and its associated file.
    
    This will remove the document record from the database and delete
    the associated file from storage.
    
    Args:
        document_id: Document unique identifier
        db: Database session dependency
        
    Raises:
        HTTPException: If document not found or deletion fails
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        # Delete file from storage
        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # Delete database record
        db.delete(document)
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )
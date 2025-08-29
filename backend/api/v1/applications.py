"""
Application API endpoints for HSA onboarding.

This module provides REST API endpoints for managing HSA applications,
including creating, retrieving, and updating personal information.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ...core.database import get_db
from ...models.application import Application
from ...schemas.application import (
    PersonalInfoRequest,
    ApplicationResponse,
    ApplicationUpdateRequest
)

# Create router for application endpoints
router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    application_data: PersonalInfoRequest,
    db: Session = Depends(get_db)
) -> ApplicationResponse:
    """
    Create a new HSA application with personal information.
    
    This endpoint handles the first step of the HSA onboarding process,
    collecting and validating personal information required for identity
    verification and eligibility determination.
    
    Args:
        application_data: Personal information request data
        db: Database session dependency
        
    Returns:
        ApplicationResponse: Created application with masked SSN
        
    Raises:
        HTTPException: If validation fails or database error occurs
    """
    try:
        # Check if application with same SSN already exists
        existing_app = db.query(Application).filter(
            Application.social_security_number == application_data.social_security_number
        ).first()
        
        if existing_app:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Application with this Social Security Number already exists"
            )
        
        # Create new application
        db_application = Application(
            full_name=application_data.full_name,
            date_of_birth=application_data.date_of_birth,
            address_street=application_data.address_street,
            address_city=application_data.address_city,
            address_state=application_data.address_state,
            address_zip=application_data.address_zip,
            social_security_number=application_data.social_security_number,
            employer_name=application_data.employer_name,
            status="pending"
        )
        
        db.add(db_application)
        db.commit()
        db.refresh(db_application)
        
        # Convert to response model (automatically masks SSN)
        return ApplicationResponse(
            id=str(db_application.id),
            full_name=db_application.full_name,
            date_of_birth=db_application.date_of_birth,
            address_street=db_application.address_street,
            address_city=db_application.address_city,
            address_state=db_application.address_state,
            address_zip=db_application.address_zip,
            social_security_number=db_application.social_security_number,  # Will be masked by validator
            employer_name=db_application.employer_name,
            status=db_application.status,
            created_at=db_application.created_at,
            updated_at=db_application.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create application"
        )


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: str,
    db: Session = Depends(get_db)
) -> ApplicationResponse:
    """
    Retrieve an HSA application by ID.
    
    Args:
        application_id: Application unique identifier
        db: Database session dependency
        
    Returns:
        ApplicationResponse: Application data with masked SSN
        
    Raises:
        HTTPException: If application not found
    """
    db_application = db.query(Application).filter(
        Application.id == application_id
    ).first()
    
    if not db_application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    return ApplicationResponse(
        id=str(db_application.id),
        full_name=db_application.full_name,
        date_of_birth=db_application.date_of_birth,
        address_street=db_application.address_street,
        address_city=db_application.address_city,
        address_state=db_application.address_state,
        address_zip=db_application.address_zip,
        social_security_number=db_application.social_security_number,  # Will be masked by validator
        employer_name=db_application.employer_name,
        status=db_application.status,
        created_at=db_application.created_at,
        updated_at=db_application.updated_at
    )


@router.put("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: str,
    update_data: ApplicationUpdateRequest,
    db: Session = Depends(get_db)
) -> ApplicationResponse:
    """
    Update an existing HSA application.
    
    Allows updating personal information for applications that are still
    in pending status. Applications that have progressed beyond the initial
    stage cannot be modified.
    
    Args:
        application_id: Application unique identifier
        update_data: Fields to update (only provided fields will be updated)
        db: Database session dependency
        
    Returns:
        ApplicationResponse: Updated application data with masked SSN
        
    Raises:
        HTTPException: If application not found or cannot be updated
    """
    db_application = db.query(Application).filter(
        Application.id == application_id
    ).first()
    
    if not db_application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check if application can be updated (only pending applications)
    if db_application.status not in ["pending"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot update application in '{db_application.status}' status"
        )
    
    try:
        # Update only provided fields
        update_dict = update_data.dict(exclude_unset=True)
        
        for field, value in update_dict.items():
            if hasattr(db_application, field):
                setattr(db_application, field, value)
        
        # Update timestamp
        db_application.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_application)
        
        return ApplicationResponse(
            id=str(db_application.id),
            full_name=db_application.full_name,
            date_of_birth=db_application.date_of_birth,
            address_street=db_application.address_street,
            address_city=db_application.address_city,
            address_state=db_application.address_state,
            address_zip=db_application.address_zip,
            social_security_number=db_application.social_security_number,  # Will be masked by validator
            employer_name=db_application.employer_name,
            status=db_application.status,
            created_at=db_application.created_at,
            updated_at=db_application.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update application"
        )


@router.get("/", response_model=List[ApplicationResponse])
def list_applications(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> List[ApplicationResponse]:
    """
    List HSA applications with optional filtering.
    
    Args:
        status: Optional status filter (pending, processing, approved, rejected, manual_review)
        limit: Maximum number of applications to return (default: 100)
        offset: Number of applications to skip (default: 0)
        db: Database session dependency
        
    Returns:
        List[ApplicationResponse]: List of applications with masked SSNs
    """
    query = db.query(Application)
    
    if status:
        query = query.filter(Application.status == status)
    
    applications = query.order_by(Application.created_at.desc()).offset(offset).limit(limit).all()
    
    return [
        ApplicationResponse(
            id=str(app.id),
            full_name=app.full_name,
            date_of_birth=app.date_of_birth,
            address_street=app.address_street,
            address_city=app.address_city,
            address_state=app.address_state,
            address_zip=app.address_zip,
            social_security_number=app.social_security_number,  # Will be masked by validator
            employer_name=app.employer_name,
            status=app.status,
            created_at=app.created_at,
            updated_at=app.updated_at
        )
        for app in applications
    ]


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: str,
    db: Session = Depends(get_db)
) -> None:
    """
    Delete an HSA application.
    
    Only applications in pending status can be deleted.
    This is primarily for cleanup and testing purposes.
    
    Args:
        application_id: Application unique identifier
        db: Database session dependency
        
    Raises:
        HTTPException: If application not found or cannot be deleted
    """
    db_application = db.query(Application).filter(
        Application.id == application_id
    ).first()
    
    if not db_application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Only allow deletion of pending applications
    if db_application.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete application in '{db_application.status}' status"
        )
    
    try:
        db.delete(db_application)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete application"
        )
"""
Application model for storing HSA application data.

This module defines the SQLAlchemy model for applications, representing
the personal information collected during the onboarding process.
"""

from datetime import date
from sqlalchemy import Column, Date, String, Text
from sqlalchemy.schema import Index
from sqlalchemy.orm import relationship

from ..core.database import BaseModel


class Application(BaseModel):
    """
    Application model for HSA onboarding.
    
    Stores personal information collected during the first step of the
    onboarding process. This data will be used for identity verification
    and eligibility determination.
    
    Attributes:
        full_name: Applicant's full legal name
        date_of_birth: Applicant's date of birth
        address_street: Street address
        address_city: City
        address_state: State (2-letter abbreviation)
        address_zip: ZIP or postal code
        social_security_number: SSN or other ID number
        employer_name: Current employer name
        status: Application status (pending, processing, approved, rejected, manual_review)
    """
    __tablename__ = "applications"
    
    # Personal information
    full_name = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Applicant's full legal name"
    )
    
    date_of_birth = Column(
        Date,
        nullable=False,
        comment="Applicant's date of birth"
    )
    
    # Address information
    address_street = Column(
        String(200),
        nullable=False,
        comment="Street address"
    )
    
    address_city = Column(
        String(50),
        nullable=False,
        comment="City"
    )
    
    address_state = Column(
        String(2),
        nullable=False,
        comment="State (2-letter abbreviation)"
    )
    
    address_zip = Column(
        String(10),
        nullable=False,
        comment="ZIP or postal code"
    )
    
    # Identification
    social_security_number = Column(
        String(11),
        nullable=False,
        comment="Social Security Number or ID number"
    )
    
    # Employment information
    employer_name = Column(
        String(100),
        nullable=False,
        comment="Current employer name"
    )
    
    # Application status
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
        comment="Application processing status"
    )
    
    # Relationships
    documents = relationship("Document", back_populates="application")
    
    # Additional indexes for performance
    __table_args__ = (
        Index("idx_applications_status_created", "status", "created_at"),
        Index("idx_applications_ssn_hash", "social_security_number"),
    )
    
    def __repr__(self) -> str:
        """String representation of the application."""
        return f"<Application(id={self.id}, name='{self.full_name}', status='{self.status}')>"
    
    def to_dict(self) -> dict:
        """Convert application to dictionary representation."""
        return {
            "id": str(self.id),
            "full_name": self.full_name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "address_street": self.address_street,
            "address_city": self.address_city,
            "address_state": self.address_state,
            "address_zip": self.address_zip,
            "social_security_number": self.social_security_number,
            "employer_name": self.employer_name,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
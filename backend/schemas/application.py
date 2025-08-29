"""
Application schemas for data validation and serialization.

This module defines Pydantic models for application data transfer objects (DTOs),
providing validation, serialization, and documentation for the API endpoints.
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
import re


class AddressInfo(BaseModel):
    """Address information schema."""
    
    street: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Street address",
        example="123 Main Street"
    )
    
    city: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="City name",
        example="Anytown"
    )
    
    state: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="State abbreviation (2 letters)",
        example="CA"
    )
    
    zip_code: str = Field(
        ...,
        min_length=5,
        max_length=10,
        description="ZIP or postal code",
        example="12345"
    )
    
    @validator('state')
    def validate_state(cls, v):
        """Validate state is uppercase 2-letter code."""
        if not re.match(r'^[A-Z]{2}$', v):
            raise ValueError('State must be a 2-letter uppercase abbreviation')
        return v
    
    @validator('zip_code')
    def validate_zip_code(cls, v):
        """Validate ZIP code format."""
        if not re.match(r'^\d{5}(-\d{4})?$', v):
            raise ValueError('ZIP code must be in format XXXXX or XXXXX-XXXX')
        return v


class PersonalInfoRequest(BaseModel):
    """Personal information request schema for creating applications."""
    
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Applicant's full legal name",
        example="John Doe"
    )
    
    date_of_birth: date = Field(
        ...,
        description="Applicant's date of birth",
        example="1990-01-15"
    )
    
    address_street: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Street address",
        example="123 Main Street"
    )
    
    address_city: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="City name",
        example="Anytown"
    )
    
    address_state: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="State abbreviation (2 letters)",
        example="CA"
    )
    
    address_zip: str = Field(
        ...,
        min_length=5,
        max_length=10,
        description="ZIP or postal code",
        example="12345"
    )
    
    social_security_number: str = Field(
        ...,
        min_length=9,
        max_length=11,
        description="Social Security Number",
        example="123-45-6789"
    )
    
    employer_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Current employer name",
        example="Acme Corporation"
    )
    
    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        """Validate date of birth is not in the future and person is at least 18."""
        today = date.today()
        if v >= today:
            raise ValueError('Date of birth cannot be in the future')
        
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError('Applicant must be at least 18 years old')
        if age > 120:
            raise ValueError('Invalid date of birth')
        
        return v
    
    @validator('address_state')
    def validate_state(cls, v):
        """Validate state is uppercase 2-letter code."""
        v = v.upper()
        if not re.match(r'^[A-Z]{2}$', v):
            raise ValueError('State must be a 2-letter abbreviation')
        return v
    
    @validator('address_zip')
    def validate_zip_code(cls, v):
        """Validate ZIP code format."""
        if not re.match(r'^\d{5}(-\d{4})?$', v):
            raise ValueError('ZIP code must be in format XXXXX or XXXXX-XXXX')
        return v
    
    @validator('social_security_number')
    def validate_ssn(cls, v):
        """Validate Social Security Number format."""
        # Remove any non-digit characters for validation
        digits_only = re.sub(r'\D', '', v)
        if len(digits_only) != 9:
            raise ValueError('Social Security Number must contain exactly 9 digits')
        
        # Check for invalid patterns
        if (digits_only == '000000000' or 
            digits_only.startswith('000') or
            digits_only[3:5] == '00' or
            digits_only[5:] == '0000'):
            raise ValueError('Invalid Social Security Number format')
        
        return v
    
    @validator('full_name', 'employer_name')
    def validate_text_fields(cls, v):
        """Validate text fields don't contain invalid characters."""
        if not re.match(r'^[a-zA-Z\s\-\.\,\']+$', v.strip()):
            raise ValueError('Field contains invalid characters')
        return v.strip()


class ApplicationResponse(BaseModel):
    """Application response schema."""
    
    id: str = Field(
        ...,
        description="Application unique identifier"
    )
    
    full_name: str = Field(
        ...,
        description="Applicant's full legal name"
    )
    
    date_of_birth: date = Field(
        ...,
        description="Applicant's date of birth"
    )
    
    address_street: str = Field(
        ...,
        description="Street address"
    )
    
    address_city: str = Field(
        ...,
        description="City name"
    )
    
    address_state: str = Field(
        ...,
        description="State abbreviation"
    )
    
    address_zip: str = Field(
        ...,
        description="ZIP or postal code"
    )
    
    social_security_number: str = Field(
        ...,
        description="Social Security Number (masked)"
    )
    
    employer_name: str = Field(
        ...,
        description="Current employer name"
    )
    
    status: str = Field(
        ...,
        description="Application status",
        example="pending"
    )
    
    created_at: datetime = Field(
        ...,
        description="When the application was created"
    )
    
    updated_at: datetime = Field(
        ...,
        description="When the application was last updated"
    )
    
    @validator('social_security_number', pre=False, always=True)
    def mask_ssn(cls, v):
        """Mask SSN for security (show only last 4 digits)."""
        if len(v) >= 4:
            return f"***-**-{v[-4:]}"
        return "***-**-****"


class ApplicationUpdateRequest(BaseModel):
    """Schema for updating application information."""
    
    full_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Applicant's full legal name"
    )
    
    date_of_birth: Optional[date] = Field(
        None,
        description="Applicant's date of birth"
    )
    
    address_street: Optional[str] = Field(
        None,
        min_length=5,
        max_length=200,
        description="Street address"
    )
    
    address_city: Optional[str] = Field(
        None,
        min_length=2,
        max_length=50,
        description="City name"
    )
    
    address_state: Optional[str] = Field(
        None,
        min_length=2,
        max_length=2,
        description="State abbreviation (2 letters)"
    )
    
    address_zip: Optional[str] = Field(
        None,
        min_length=5,
        max_length=10,
        description="ZIP or postal code"
    )
    
    employer_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Current employer name"
    )
    
    # Apply the same validators as PersonalInfoRequest but for optional fields
    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        """Validate date of birth if provided."""
        if v is None:
            return v
        
        today = date.today()
        if v >= today:
            raise ValueError('Date of birth cannot be in the future')
        
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError('Applicant must be at least 18 years old')
        if age > 120:
            raise ValueError('Invalid date of birth')
        
        return v
    
    @validator('address_state')
    def validate_state(cls, v):
        """Validate state if provided."""
        if v is None:
            return v
        
        v = v.upper()
        if not re.match(r'^[A-Z]{2}$', v):
            raise ValueError('State must be a 2-letter abbreviation')
        return v
    
    @validator('address_zip')
    def validate_zip_code(cls, v):
        """Validate ZIP code if provided."""
        if v is None:
            return v
        
        if not re.match(r'^\d{5}(-\d{4})?$', v):
            raise ValueError('ZIP code must be in format XXXXX or XXXXX-XXXX')
        return v
    
    @validator('full_name', 'employer_name')
    def validate_text_fields(cls, v):
        """Validate text fields if provided."""
        if v is None:
            return v
        
        if not re.match(r'^[a-zA-Z\s\-\.\,\']+$', v.strip()):
            raise ValueError('Field contains invalid characters')
        return v.strip()
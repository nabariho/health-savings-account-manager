"""
Unit tests for Pydantic schemas and validation.

Tests the PersonalInfoRequest and ApplicationResponse schemas
to ensure proper validation of user input data.
"""

import pytest
from datetime import date, datetime
from pydantic import ValidationError

from backend.schemas.application import PersonalInfoRequest, ApplicationResponse


class TestPersonalInfoRequest:
    """Test PersonalInfoRequest schema validation."""
    
    def test_valid_personal_info_request(self):
        """Test validation with valid personal information."""
        valid_data = {
            "full_name": "John Doe",
            "date_of_birth": "1990-01-15",
            "address_street": "123 Main Street",
            "address_city": "Anytown",
            "address_state": "CA",
            "address_zip": "12345",
            "social_security_number": "123-45-6789",
            "employer_name": "Acme Corporation"
        }
        
        request = PersonalInfoRequest(**valid_data)
        
        assert request.full_name == "John Doe"
        assert request.date_of_birth == date(1990, 1, 15)
        assert request.address_street == "123 Main Street"
        assert request.address_city == "Anytown"
        assert request.address_state == "CA"
        assert request.address_zip == "12345"
        assert request.social_security_number == "123-45-6789"
        assert request.employer_name == "Acme Corporation"
    
    def test_invalid_full_name_too_short(self):
        """Test validation fails for name too short."""
        with pytest.raises(ValidationError) as exc_info:
            PersonalInfoRequest(
                full_name="J",
                date_of_birth="1990-01-15",
                address_street="123 Main Street",
                address_city="Anytown",
                address_state="CA",
                address_zip="12345",
                social_security_number="123-45-6789",
                employer_name="Acme Corporation"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('full_name',) for error in errors)
    
    def test_invalid_full_name_too_long(self):
        """Test validation fails for name too long."""
        long_name = "A" * 101
        
        with pytest.raises(ValidationError) as exc_info:
            PersonalInfoRequest(
                full_name=long_name,
                date_of_birth="1990-01-15",
                address_street="123 Main Street",
                address_city="Anytown",
                address_state="CA",
                address_zip="12345",
                social_security_number="123-45-6789",
                employer_name="Acme Corporation"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('full_name',) for error in errors)
    
    def test_invalid_date_of_birth_future(self):
        """Test validation fails for future date of birth."""
        future_date = "2050-01-01"
        
        with pytest.raises(ValidationError) as exc_info:
            PersonalInfoRequest(
                full_name="John Doe",
                date_of_birth=future_date,
                address_street="123 Main Street",
                address_city="Anytown",
                address_state="CA",
                address_zip="12345",
                social_security_number="123-45-6789",
                employer_name="Acme Corporation"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('date_of_birth',) for error in errors)
    
    def test_invalid_date_of_birth_too_young(self):
        """Test validation fails for applicant under 18."""
        recent_date = date.today().replace(year=date.today().year - 17).strftime("%Y-%m-%d")
        
        with pytest.raises(ValidationError) as exc_info:
            PersonalInfoRequest(
                full_name="John Doe",
                date_of_birth=recent_date,
                address_street="123 Main Street",
                address_city="Anytown",
                address_state="CA",
                address_zip="12345",
                social_security_number="123-45-6789",
                employer_name="Acme Corporation"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('date_of_birth',) for error in errors)
    
    def test_invalid_state_format(self):
        """Test validation fails for invalid state format."""
        with pytest.raises(ValidationError) as exc_info:
            PersonalInfoRequest(
                full_name="John Doe",
                date_of_birth="1990-01-15",
                address_street="123 Main Street",
                address_city="Anytown",
                address_state="California",  # Should be 2-letter abbreviation
                address_zip="12345",
                social_security_number="123-45-6789",
                employer_name="Acme Corporation"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('address_state',) for error in errors)
    
    def test_state_auto_uppercase(self):
        """Test state is automatically converted to uppercase."""
        request = PersonalInfoRequest(
            full_name="John Doe",
            date_of_birth="1990-01-15",
            address_street="123 Main Street",
            address_city="Anytown",
            address_state="ca",  # lowercase
            address_zip="12345",
            social_security_number="123-45-6789",
            employer_name="Acme Corporation"
        )
        
        assert request.address_state == "CA"
    
    def test_invalid_zip_code_format(self):
        """Test validation fails for invalid ZIP code format."""
        with pytest.raises(ValidationError) as exc_info:
            PersonalInfoRequest(
                full_name="John Doe",
                date_of_birth="1990-01-15",
                address_street="123 Main Street",
                address_city="Anytown",
                address_state="CA",
                address_zip="1234",  # Too short
                social_security_number="123-45-6789",
                employer_name="Acme Corporation"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('address_zip',) for error in errors)
    
    def test_valid_extended_zip_code(self):
        """Test validation passes for extended ZIP+4 format."""
        request = PersonalInfoRequest(
            full_name="John Doe",
            date_of_birth="1990-01-15",
            address_street="123 Main Street",
            address_city="Anytown",
            address_state="CA",
            address_zip="12345-6789",
            social_security_number="123-45-6789",
            employer_name="Acme Corporation"
        )
        
        assert request.address_zip == "12345-6789"
    
    def test_invalid_ssn_format(self):
        """Test validation fails for invalid SSN format."""
        with pytest.raises(ValidationError) as exc_info:
            PersonalInfoRequest(
                full_name="John Doe",
                date_of_birth="1990-01-15",
                address_street="123 Main Street",
                address_city="Anytown",
                address_state="CA",
                address_zip="12345",
                social_security_number="123-45-67890",  # Too many digits
                employer_name="Acme Corporation"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('social_security_number',) for error in errors)
    
    def test_invalid_ssn_all_zeros(self):
        """Test validation fails for invalid SSN patterns."""
        with pytest.raises(ValidationError) as exc_info:
            PersonalInfoRequest(
                full_name="John Doe",
                date_of_birth="1990-01-15",
                address_street="123 Main Street",
                address_city="Anytown",
                address_state="CA",
                address_zip="12345",
                social_security_number="000-00-0000",
                employer_name="Acme Corporation"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('social_security_number',) for error in errors)
    
    def test_text_field_with_invalid_characters(self):
        """Test validation fails for text fields with invalid characters."""
        with pytest.raises(ValidationError) as exc_info:
            PersonalInfoRequest(
                full_name="John@Doe",  # Contains invalid character
                date_of_birth="1990-01-15",
                address_street="123 Main Street",
                address_city="Anytown",
                address_state="CA",
                address_zip="12345",
                social_security_number="123-45-6789",
                employer_name="Acme Corporation"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('full_name',) for error in errors)


class TestApplicationResponse:
    """Test ApplicationResponse schema."""
    
    def test_valid_application_response(self):
        """Test ApplicationResponse with valid data."""
        response_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "full_name": "John Doe",
            "date_of_birth": date(1990, 1, 15),
            "address_street": "123 Main Street",
            "address_city": "Anytown",
            "address_state": "CA",
            "address_zip": "12345",
            "social_security_number": "123-45-6789",
            "employer_name": "Acme Corporation",
            "status": "pending",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        response = ApplicationResponse(**response_data)
        
        assert response.id == "123e4567-e89b-12d3-a456-426614174000"
        assert response.full_name == "John Doe"
        assert response.status == "pending"
    
    def test_ssn_masking(self):
        """Test SSN is masked in response."""
        response_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "full_name": "John Doe",
            "date_of_birth": date(1990, 1, 15),
            "address_street": "123 Main Street",
            "address_city": "Anytown",
            "address_state": "CA",
            "address_zip": "12345",
            "social_security_number": "123-45-6789",
            "employer_name": "Acme Corporation",
            "status": "pending",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        response = ApplicationResponse(**response_data)
        
        # SSN should be masked to show only last 4 digits
        assert response.social_security_number == "***-**-6789"
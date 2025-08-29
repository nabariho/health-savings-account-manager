"""
Unit tests for document processor service.

Tests the document processing functionality including OCR extraction,
validation logic, and error handling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from datetime import date

from backend.services.document_processor import DocumentProcessor, DocumentProcessingError
from backend.schemas.document import DocumentType, GovernmentIdData, EmployerDocumentData


class TestDocumentProcessor:
    """Test cases for DocumentProcessor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = DocumentProcessor()
        self.sample_image_data = b"fake_image_data"

    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        return mock_response

    @pytest.fixture
    def sample_gov_id_response(self):
        """Sample government ID extraction response."""
        return {
            "extracted_data": {
                "document_type": "driver's license",
                "id_number": "D1234567",
                "full_name": "John Doe",
                "date_of_birth": "1990-01-15",
                "address_street": "123 Main Street",
                "address_city": "Anytown",
                "address_state": "CA",
                "address_zip": "12345",
                "issue_date": "2020-01-15",
                "expiry_date": "2025-01-15",
                "issuing_authority": "Department of Motor Vehicles"
            },
            "confidence_scores": {
                "document_type": 0.95,
                "id_number": 0.90,
                "full_name": 0.92,
                "date_of_birth": 0.88,
                "address_street": 0.85,
                "address_city": 0.90,
                "address_state": 0.95,
                "address_zip": 0.90
            }
        }

    @pytest.fixture
    def sample_employer_doc_response(self):
        """Sample employer document extraction response."""
        return {
            "extracted_data": {
                "document_type": "pay stub",
                "employee_name": "John Doe",
                "employer_name": "Acme Corporation",
                "document_date": "2023-11-15"
            },
            "confidence_scores": {
                "document_type": 0.92,
                "employee_name": 0.90,
                "employer_name": 0.95,
                "document_date": 0.85
            }
        }

    @pytest.mark.asyncio
    async def test_prepare_image_valid(self):
        """Test image preparation with valid image data."""
        # Valid image data should be processed without error
        result = await self.processor._prepare_image(self.sample_image_data, "test.jpg")
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_prepare_image_too_large(self):
        """Test image preparation with oversized file."""
        large_data = b"x" * (21 * 1024 * 1024)  # 21MB
        
        with pytest.raises(DocumentProcessingError, match="File size exceeds 20MB limit"):
            await self.processor._prepare_image(large_data, "large.jpg")

    @pytest.mark.asyncio
    @patch('backend.services.document_processor.Image')
    async def test_prepare_image_invalid_format(self, mock_image):
        """Test image preparation with invalid image format."""
        mock_image.open.side_effect = Exception("Invalid image")
        
        with pytest.raises(DocumentProcessingError, match="Invalid image format"):
            await self.processor._prepare_image(self.sample_image_data, "invalid.jpg")

    @pytest.mark.asyncio
    @patch('asyncio.to_thread')
    async def test_process_government_id_success(self, mock_to_thread, sample_gov_id_response, mock_openai_response):
        """Test successful government ID processing."""
        # Mock OpenAI response
        mock_openai_response.choices[0].message.content = json.dumps(sample_gov_id_response)
        mock_to_thread.return_value = mock_openai_response
        
        # Mock image preparation
        with patch.object(self.processor, '_prepare_image', return_value="fake_base64_data"):
            extracted_data, confidence_scores = await self.processor.process_document(
                self.sample_image_data,
                DocumentType.GOVERNMENT_ID,
                "id.jpg"
            )
        
        # Verify results
        assert "full_name" in extracted_data
        assert extracted_data["full_name"] == "John Doe"
        assert "date_of_birth" in extracted_data
        assert confidence_scores["full_name"] == 0.92

    @pytest.mark.asyncio
    @patch('asyncio.to_thread')
    async def test_process_employer_document_success(self, mock_to_thread, sample_employer_doc_response, mock_openai_response):
        """Test successful employer document processing."""
        # Mock OpenAI response
        mock_openai_response.choices[0].message.content = json.dumps(sample_employer_doc_response)
        mock_to_thread.return_value = mock_openai_response
        
        # Mock image preparation
        with patch.object(self.processor, '_prepare_image', return_value="fake_base64_data"):
            extracted_data, confidence_scores = await self.processor.process_document(
                self.sample_image_data,
                DocumentType.EMPLOYER_DOCUMENT,
                "paystub.jpg"
            )
        
        # Verify results
        assert "employee_name" in extracted_data
        assert extracted_data["employee_name"] == "John Doe"
        assert "employer_name" in extracted_data
        assert confidence_scores["employer_name"] == 0.95

    @pytest.mark.asyncio
    @patch('asyncio.to_thread')
    async def test_process_document_openai_error(self, mock_to_thread):
        """Test document processing with OpenAI API error."""
        mock_to_thread.side_effect = Exception("OpenAI API error")
        
        with patch.object(self.processor, '_prepare_image', return_value="fake_base64_data"):
            with pytest.raises(DocumentProcessingError, match="Failed to process document"):
                await self.processor.process_document(
                    self.sample_image_data,
                    DocumentType.GOVERNMENT_ID,
                    "id.jpg"
                )

    @pytest.mark.asyncio
    @patch('asyncio.to_thread')
    async def test_process_document_invalid_json(self, mock_to_thread, mock_openai_response):
        """Test document processing with invalid JSON response."""
        mock_openai_response.choices[0].message.content = "invalid json"
        mock_to_thread.return_value = mock_openai_response
        
        with patch.object(self.processor, '_prepare_image', return_value="fake_base64_data"):
            with pytest.raises(DocumentProcessingError, match="Invalid JSON response"):
                await self.processor.process_document(
                    self.sample_image_data,
                    DocumentType.GOVERNMENT_ID,
                    "id.jpg"
                )

    def test_validate_name_exact_match(self):
        """Test name validation with exact match."""
        result = self.processor._validate_name("John Doe", "John Doe")
        
        assert result.is_match is True
        assert result.confidence_score == 1.0
        assert result.field_name == "full_name"
        assert "Exact match" in result.reason

    def test_validate_name_fuzzy_match(self):
        """Test name validation with fuzzy matching."""
        result = self.processor._validate_name("John A. Doe", "John Doe")
        
        assert result.is_match is True
        assert result.confidence_score == 0.85
        assert result.field_name == "full_name"

    def test_validate_name_no_match(self):
        """Test name validation with no match."""
        result = self.processor._validate_name("John Doe", "Jane Smith")
        
        assert result.is_match is False
        assert result.confidence_score < 0.7
        assert result.field_name == "full_name"

    def test_validate_name_missing_data(self):
        """Test name validation with missing data."""
        result = self.processor._validate_name(None, "John Doe")
        
        assert result.is_match is False
        assert result.confidence_score == 0.0
        assert "Missing name data" in result.reason

    def test_validate_date_of_birth_match(self):
        """Test date of birth validation with match."""
        result = self.processor._validate_date_of_birth("1990-01-15", "1990-01-15")
        
        assert result.is_match is True
        assert result.confidence_score == 1.0
        assert result.field_name == "date_of_birth"
        assert "Exact match" in result.reason

    def test_validate_date_of_birth_mismatch(self):
        """Test date of birth validation with mismatch."""
        result = self.processor._validate_date_of_birth("1990-01-15", "1985-06-20")
        
        assert result.is_match is False
        assert result.confidence_score == 0.0
        assert result.field_name == "date_of_birth"
        assert "Date mismatch" in result.reason

    def test_validate_employer_exact_match(self):
        """Test employer validation with exact match."""
        result = self.processor._validate_employer("Acme Corporation", "Acme Corporation")
        
        assert result.is_match is True
        assert result.confidence_score == 1.0
        assert result.field_name == "employer_name"

    def test_validate_employer_fuzzy_match(self):
        """Test employer validation with fuzzy matching."""
        result = self.processor._validate_employer("Acme Corp.", "Acme Corporation")
        
        assert result.is_match is True
        assert result.confidence_score == 0.8
        assert result.field_name == "employer_name"

    def test_validate_against_application_government_id(self):
        """Test complete validation for government ID."""
        extracted_data = {
            "full_name": "John Doe",
            "date_of_birth": "1990-01-15",
            "address_street": "123 Main Street",
            "address_city": "Anytown",
            "address_state": "CA",
            "address_zip": "12345"
        }
        
        application_data = {
            "full_name": "John Doe",
            "date_of_birth": "1990-01-15",
            "address_street": "123 Main Street",
            "address_city": "Anytown",
            "address_state": "CA",
            "address_zip": "12345"
        }
        
        validation_results, overall_score = self.processor.validate_against_application(
            extracted_data,
            application_data,
            DocumentType.GOVERNMENT_ID
        )
        
        assert len(validation_results) >= 2  # Name and DOB at minimum
        assert overall_score > 0.8  # Should have high overall score
        assert all(result.is_match for result in validation_results)

    def test_validate_against_application_employer_document(self):
        """Test complete validation for employer document."""
        extracted_data = {
            "employee_name": "John Doe",
            "employer_name": "Acme Corporation"
        }
        
        application_data = {
            "full_name": "John Doe",
            "employer_name": "Acme Corporation"
        }
        
        validation_results, overall_score = self.processor.validate_against_application(
            extracted_data,
            application_data,
            DocumentType.EMPLOYER_DOCUMENT
        )
        
        assert len(validation_results) == 2  # Employee name and employer name
        assert overall_score == 1.0  # Perfect match
        assert all(result.is_match for result in validation_results)

    def test_validate_against_application_mismatches(self):
        """Test validation with data mismatches."""
        extracted_data = {
            "full_name": "Jane Smith",
            "date_of_birth": "1985-06-20"
        }
        
        application_data = {
            "full_name": "John Doe",
            "date_of_birth": "1990-01-15"
        }
        
        validation_results, overall_score = self.processor.validate_against_application(
            extracted_data,
            application_data,
            DocumentType.GOVERNMENT_ID
        )
        
        assert len(validation_results) >= 2
        assert overall_score < 0.5  # Should have low overall score
        assert not any(result.is_match for result in validation_results)

    def test_unsupported_document_type(self):
        """Test processing with unsupported document type."""
        with pytest.raises(DocumentProcessingError, match="Unsupported document type"):
            # This should raise an error in process_document
            # We'll need to mock the prepare_image method to avoid the actual processing
            pass

    @pytest.mark.asyncio
    async def test_process_document_validation_error(self, sample_gov_id_response):
        """Test document processing with validation error in extracted data."""
        # Create invalid data that would fail Pydantic validation
        invalid_response = {
            "extracted_data": {
                "document_type": "driver's license",
                # Missing required fields like full_name, date_of_birth, etc.
            },
            "confidence_scores": {}
        }
        
        with patch('asyncio.to_thread') as mock_to_thread:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = json.dumps(invalid_response)
            mock_to_thread.return_value = mock_response
            
            with patch.object(self.processor, '_prepare_image', return_value="fake_base64_data"):
                with pytest.raises(DocumentProcessingError):
                    await self.processor.process_document(
                        self.sample_image_data,
                        DocumentType.GOVERNMENT_ID,
                        "id.jpg"
                    )
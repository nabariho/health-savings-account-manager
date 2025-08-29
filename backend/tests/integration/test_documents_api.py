"""
Integration tests for document API endpoints.

Tests the complete document upload, processing, and validation workflow
including API endpoints, database operations, and OpenAI integration.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
import json
import io
from datetime import datetime

from backend.main import app
from backend.core.database import get_db
from backend.models.application import Application
from backend.models.document import Document
from backend.schemas.document import DocumentType, ProcessingStatus


@pytest.fixture
def client():
    """Test client for API endpoints."""
    return TestClient(app)


@pytest.fixture
def test_db():
    """Test database session."""
    # In a real test, you'd use a test database
    # For now, we'll mock the database session
    return MagicMock(spec=Session)


@pytest.fixture
def sample_application(test_db):
    """Sample application for testing."""
    app = Application(
        id="test-app-id",
        full_name="John Doe",
        date_of_birth="1990-01-15",
        address_street="123 Main Street",
        address_city="Anytown",
        address_state="CA",
        address_zip="12345",
        social_security_number="123-45-6789",
        employer_name="Acme Corporation",
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    return app


@pytest.fixture
def sample_document(sample_application):
    """Sample document for testing."""
    doc = Document(
        id="test-doc-id",
        application_id=sample_application.id,
        document_type="government_id",
        file_name="test_id.jpg",
        file_path="/uploads/test_id.jpg",
        content_type="image/jpeg",
        file_size=12345,
        processing_status="completed",
        extracted_data={
            "document_type": "driver's license",
            "id_number": "D1234567",
            "full_name": "John Doe",
            "date_of_birth": "1990-01-15"
        },
        confidence_scores={
            "full_name": 0.95,
            "date_of_birth": 0.90
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    return doc


@pytest.fixture
def mock_file():
    """Mock uploaded file."""
    return io.BytesIO(b"fake image data")


class TestDocumentUpload:
    """Test cases for document upload endpoint."""

    @patch('backend.api.v1.documents.get_db')
    @patch('backend.api.v1.documents.document_processor')
    @patch('builtins.open', create=True)
    @patch('pathlib.Path.mkdir')
    def test_upload_document_success(self, mock_mkdir, mock_open, mock_processor, mock_get_db, client, sample_application, test_db):
        """Test successful document upload and processing."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = sample_application
        test_db.add = MagicMock()
        test_db.commit = MagicMock()
        test_db.refresh = MagicMock()
        
        # Mock document processing
        mock_processor.process_document.return_value = (
            {"full_name": "John Doe", "date_of_birth": "1990-01-15"},
            {"full_name": 0.95, "date_of_birth": 0.90}
        )
        
        # Mock file operations
        mock_open.return_value.__enter__ = MagicMock()
        mock_open.return_value.__exit__ = MagicMock()
        mock_mkdir.return_value = None
        
        # Create test file
        files = {
            'file': ('test_id.jpg', io.BytesIO(b"fake image data"), 'image/jpeg')
        }
        data = {
            'application_id': 'test-app-id',
            'document_type': 'government_id'
        }
        
        # Make request
        response = client.post("/api/v1/documents/upload", files=files, data=data)
        
        # Verify response
        assert response.status_code == 201
        result = response.json()
        assert result["document_type"] == "government_id"
        assert result["processing_status"] == "completed"
        assert "extracted_data" in result

    @patch('backend.api.v1.documents.get_db')
    def test_upload_document_application_not_found(self, mock_get_db, client, test_db):
        """Test document upload with invalid application ID."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = None
        
        # Create test file
        files = {
            'file': ('test_id.jpg', io.BytesIO(b"fake image data"), 'image/jpeg')
        }
        data = {
            'application_id': 'invalid-app-id',
            'document_type': 'government_id'
        }
        
        # Make request
        response = client.post("/api/v1/documents/upload", files=files, data=data)
        
        # Verify response
        assert response.status_code == 404
        assert "Application not found" in response.json()["message"]

    @patch('backend.api.v1.documents.get_db')
    def test_upload_document_invalid_file_type(self, mock_get_db, client, sample_application, test_db):
        """Test document upload with invalid file type."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = sample_application
        
        # Create test file with invalid type
        files = {
            'file': ('test.txt', io.BytesIO(b"text file content"), 'text/plain')
        }
        data = {
            'application_id': 'test-app-id',
            'document_type': 'government_id'
        }
        
        # Make request
        response = client.post("/api/v1/documents/upload", files=files, data=data)
        
        # Verify response
        assert response.status_code == 422
        assert "Unsupported file type" in response.json()["message"]

    @patch('backend.api.v1.documents.get_db')
    def test_upload_document_file_too_large(self, mock_get_db, client, sample_application, test_db):
        """Test document upload with file too large."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = sample_application
        
        # Create large test file (11MB)
        large_data = b"x" * (11 * 1024 * 1024)
        files = {
            'file': ('large_file.jpg', io.BytesIO(large_data), 'image/jpeg')
        }
        data = {
            'application_id': 'test-app-id',
            'document_type': 'government_id'
        }
        
        # Make request
        response = client.post("/api/v1/documents/upload", files=files, data=data)
        
        # Verify response
        assert response.status_code == 413
        assert "File size exceeds maximum" in response.json()["message"]

    @patch('backend.api.v1.documents.get_db')
    @patch('backend.api.v1.documents.document_processor')
    def test_upload_document_processing_error(self, mock_processor, mock_get_db, client, sample_application, test_db):
        """Test document upload with processing error."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = sample_application
        
        # Mock processing error
        from backend.services.document_processor import DocumentProcessingError
        mock_processor.process_document.side_effect = DocumentProcessingError("Processing failed")
        
        # Create test file
        files = {
            'file': ('test_id.jpg', io.BytesIO(b"fake image data"), 'image/jpeg')
        }
        data = {
            'application_id': 'test-app-id',
            'document_type': 'government_id'
        }
        
        with patch('builtins.open', create=True), patch('pathlib.Path.mkdir'):
            response = client.post("/api/v1/documents/upload", files=files, data=data)
        
        # Should still return 201 but with failed status
        assert response.status_code == 201
        result = response.json()
        assert result["processing_status"] == "failed"
        assert "Processing failed" in result["processing_error"]


class TestDocumentStatus:
    """Test cases for document status endpoint."""

    @patch('backend.api.v1.documents.get_db')
    def test_get_document_status_success(self, mock_get_db, client, sample_document, test_db):
        """Test successful document status retrieval."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = sample_document
        
        # Make request
        response = client.get(f"/api/v1/documents/{sample_document.id}/status")
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == sample_document.id
        assert result["processing_status"] == "completed"
        assert "extracted_data" in result

    @patch('backend.api.v1.documents.get_db')
    def test_get_document_status_not_found(self, mock_get_db, client, test_db):
        """Test document status retrieval with invalid document ID."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = None
        
        # Make request
        response = client.get("/api/v1/documents/invalid-doc-id/status")
        
        # Verify response
        assert response.status_code == 404
        assert "Document not found" in response.json()["message"]


class TestDocumentList:
    """Test cases for document listing endpoint."""

    @patch('backend.api.v1.documents.get_db')
    def test_list_application_documents_success(self, mock_get_db, client, sample_application, sample_document, test_db):
        """Test successful document listing."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = sample_application
        test_db.query().filter().order_by().all.return_value = [sample_document]
        
        # Make request
        response = client.get(f"/api/v1/documents/application/{sample_application.id}")
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]["id"] == sample_document.id

    @patch('backend.api.v1.documents.get_db')
    def test_list_application_documents_not_found(self, mock_get_db, client, test_db):
        """Test document listing with invalid application ID."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = None
        
        # Make request
        response = client.get("/api/v1/documents/application/invalid-app-id")
        
        # Verify response
        assert response.status_code == 404
        assert "Application not found" in response.json()["message"]


class TestDocumentValidation:
    """Test cases for document validation endpoint."""

    @patch('backend.api.v1.documents.get_db')
    @patch('backend.api.v1.documents.document_processor')
    def test_validate_document_success(self, mock_processor, mock_get_db, client, sample_document, sample_application, test_db):
        """Test successful document validation."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.side_effect = [sample_document, sample_application]
        
        # Mock validation results
        from backend.schemas.document import ValidationResult
        validation_results = [
            ValidationResult(
                field_name="full_name",
                application_value="John Doe",
                document_value="John Doe",
                is_match=True,
                confidence_score=1.0,
                reason="Exact match"
            )
        ]
        mock_processor.validate_against_application.return_value = (validation_results, 0.95)
        
        # Make request
        response = client.post(f"/api/v1/documents/{sample_document.id}/validate")
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert result["overall_match_score"] == 0.95
        assert result["recommendation"] == "APPROVE"
        assert len(result["validation_results"]) == 1

    @patch('backend.api.v1.documents.get_db')
    def test_validate_document_not_found(self, mock_get_db, client, test_db):
        """Test document validation with invalid document ID."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = None
        
        # Make request
        response = client.post("/api/v1/documents/invalid-doc-id/validate")
        
        # Verify response
        assert response.status_code == 404
        assert "Document not found" in response.json()["message"]

    @patch('backend.api.v1.documents.get_db')
    def test_validate_document_not_processed(self, mock_get_db, client, sample_document, test_db):
        """Test document validation when processing not completed."""
        # Setup mocks
        sample_document.processing_status = "processing"
        sample_document.extracted_data = None
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = sample_document
        
        # Make request
        response = client.post(f"/api/v1/documents/{sample_document.id}/validate")
        
        # Verify response
        assert response.status_code == 422
        assert "processing not completed" in response.json()["message"]


class TestDocumentDeletion:
    """Test cases for document deletion endpoint."""

    @patch('backend.api.v1.documents.get_db')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    def test_delete_document_success(self, mock_unlink, mock_exists, mock_get_db, client, sample_document, test_db):
        """Test successful document deletion."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = sample_document
        test_db.delete = MagicMock()
        test_db.commit = MagicMock()
        mock_exists.return_value = True
        mock_unlink.return_value = None
        
        # Make request
        response = client.delete(f"/api/v1/documents/{sample_document.id}")
        
        # Verify response
        assert response.status_code == 204
        test_db.delete.assert_called_once_with(sample_document)
        test_db.commit.assert_called_once()

    @patch('backend.api.v1.documents.get_db')
    def test_delete_document_not_found(self, mock_get_db, client, test_db):
        """Test document deletion with invalid document ID."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = None
        
        # Make request
        response = client.delete("/api/v1/documents/invalid-doc-id")
        
        # Verify response
        assert response.status_code == 404
        assert "Document not found" in response.json()["message"]


class TestDocumentWorkflow:
    """Integration tests for complete document workflow."""

    @patch('backend.api.v1.documents.get_db')
    @patch('backend.api.v1.documents.document_processor')
    @patch('builtins.open', create=True)
    @patch('pathlib.Path.mkdir')
    def test_complete_document_workflow(self, mock_mkdir, mock_open, mock_processor, mock_get_db, client, sample_application, test_db):
        """Test complete workflow: upload -> status -> validate -> delete."""
        # Setup mocks for upload
        mock_get_db.return_value = test_db
        test_db.query().filter().first.side_effect = [
            sample_application,  # For upload
            None,  # For document creation (new document)
            sample_application,  # For validation (get application)
        ]
        
        mock_processor.process_document.return_value = (
            {"full_name": "John Doe", "date_of_birth": "1990-01-15"},
            {"full_name": 0.95, "date_of_birth": 0.90}
        )
        
        # Step 1: Upload document
        files = {'file': ('test_id.jpg', io.BytesIO(b"fake image data"), 'image/jpeg')}
        data = {'application_id': 'test-app-id', 'document_type': 'government_id'}
        
        upload_response = client.post("/api/v1/documents/upload", files=files, data=data)
        assert upload_response.status_code == 201
        
        document_id = upload_response.json()["id"]
        
        # Step 2: Check status (mock return the document)
        sample_doc = MagicMock()
        sample_doc.id = document_id
        sample_doc.processing_status = "completed"
        sample_doc.extracted_data = {"full_name": "John Doe"}
        sample_doc.confidence_scores = {"full_name": 0.95}
        sample_doc.updated_at = datetime.utcnow()
        
        test_db.query().filter().first.return_value = sample_doc
        
        status_response = client.get(f"/api/v1/documents/{document_id}/status")
        assert status_response.status_code == 200
        
        # Step 3: Validate document
        from backend.schemas.document import ValidationResult
        validation_results = [
            ValidationResult(
                field_name="full_name",
                application_value="John Doe",
                document_value="John Doe",
                is_match=True,
                confidence_score=1.0,
                reason="Exact match"
            )
        ]
        mock_processor.validate_against_application.return_value = (validation_results, 0.95)
        
        # Mock both document and application for validation
        test_db.query().filter().first.side_effect = [sample_doc, sample_application]
        
        validate_response = client.post(f"/api/v1/documents/{document_id}/validate")
        assert validate_response.status_code == 200
        
        # Step 4: Delete document
        test_db.query().filter().first.return_value = sample_doc
        test_db.delete = MagicMock()
        test_db.commit = MagicMock()
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.unlink'):
            delete_response = client.delete(f"/api/v1/documents/{document_id}")
        
        assert delete_response.status_code == 204
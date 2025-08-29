"""
Integration tests for decision API endpoints.

Tests the complete decision evaluation workflow including API endpoints,
database operations, and business rule application.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
from datetime import datetime, date, timedelta

from backend.main import app
from backend.core.database import get_db
from backend.models.application import Application
from backend.models.document import Document
from backend.schemas.decision import DecisionType, DecisionConfig
from backend.schemas.document import DocumentType, ProcessingStatus


@pytest.fixture
def client():
    """Test client for API endpoints."""
    return TestClient(app)


@pytest.fixture
def test_db():
    """Test database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def sample_application(test_db):
    """Sample application for testing."""
    app = Application(
        id="test-decision-app-001",
        full_name="John Doe",
        date_of_birth=date(1990, 1, 15),
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
def sample_valid_government_id(sample_application):
    """Sample government ID document with valid data."""
    return Document(
        id="test-gov-id-001",
        application_id=sample_application.id,
        document_type=DocumentType.GOVERNMENT_ID.value,
        file_name="valid_id.jpg",
        file_path="/uploads/valid_id.jpg",
        content_type="image/jpeg",
        file_size=12345,
        processing_status=ProcessingStatus.COMPLETED.value,
        extracted_data={
            "document_type": "driver's license",
            "id_number": "D1234567",
            "full_name": "John Doe",
            "date_of_birth": "1990-01-15",
            "address_street": "123 Main Street",
            "address_city": "Anytown",
            "address_state": "CA",
            "address_zip": "12345",
            "issue_date": "2020-01-15",
            "expiry_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d"),
            "issuing_authority": "Department of Motor Vehicles"
        },
        confidence_scores={
            "full_name": 0.95,
            "date_of_birth": 0.90,
            "address_street": 0.85,
            "expiry_date": 0.95
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_expired_government_id(sample_application):
    """Sample government ID document with expired date."""
    return Document(
        id="test-expired-id-001",
        application_id=sample_application.id,
        document_type=DocumentType.GOVERNMENT_ID.value,
        file_name="expired_id.jpg",
        file_path="/uploads/expired_id.jpg",
        content_type="image/jpeg",
        file_size=12345,
        processing_status=ProcessingStatus.COMPLETED.value,
        extracted_data={
            "document_type": "driver's license",
            "id_number": "D7654321",
            "full_name": "John Doe",
            "date_of_birth": "1990-01-15",
            "expiry_date": (date.today() - timedelta(days=30)).strftime("%Y-%m-%d"),  # Expired
            "issuing_authority": "Department of Motor Vehicles"
        },
        confidence_scores={
            "full_name": 0.95,
            "date_of_birth": 0.90,
            "expiry_date": 0.95
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_mismatched_government_id(sample_application):
    """Sample government ID document with mismatched data."""
    return Document(
        id="test-mismatch-id-001",
        application_id=sample_application.id,
        document_type=DocumentType.GOVERNMENT_ID.value,
        file_name="mismatched_id.jpg",
        file_path="/uploads/mismatched_id.jpg",
        content_type="image/jpeg",
        file_size=12345,
        processing_status=ProcessingStatus.COMPLETED.value,
        extracted_data={
            "document_type": "driver's license",
            "id_number": "D9999999",
            "full_name": "Jane Smith",  # Name mismatch
            "date_of_birth": "1985-06-20",  # DOB mismatch
            "expiry_date": (date.today() + timedelta(days=180)).strftime("%Y-%m-%d"),
            "issuing_authority": "Department of Motor Vehicles"
        },
        confidence_scores={
            "full_name": 0.95,
            "date_of_birth": 0.90
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


class TestDecisionEvaluationAPI:
    """Test cases for decision evaluation endpoint."""

    @patch('backend.api.v1.decisions.get_db')
    def test_evaluate_application_approve(self, mock_get_db, client, sample_application, sample_valid_government_id, test_db):
        """Test application evaluation that results in approval."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = sample_application
        test_db.query().filter().all.return_value = [sample_valid_government_id]
        
        # Make request
        response = client.post(
            "/api/v1/decisions/evaluate",
            json={"application_id": "test-decision-app-001"}
        )
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert result["application_id"] == "test-decision-app-001"
        assert result["decision"] == "approve"
        assert result["risk_score"] <= 0.1
        assert "validation checks passed" in result["reasoning"].lower()
        assert len(result["validation_results"]) > 0
        assert result["created_at"] is not None

    @patch('backend.api.v1.decisions.get_db')
    def test_evaluate_application_reject_expired_id(self, mock_get_db, client, sample_application, sample_expired_government_id, test_db):
        """Test application evaluation that results in rejection due to expired ID."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = sample_application
        test_db.query().filter().all.return_value = [sample_expired_government_id]
        
        # Make request
        response = client.post(
            "/api/v1/decisions/evaluate",
            json={"application_id": "test-decision-app-001"}
        )
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert result["decision"] == "reject"
        assert result["risk_score"] == 1.0
        assert "expired" in result["reasoning"].lower()
        
        # Check validation results include ID expiry failure
        id_expiry_validations = [
            v for v in result["validation_results"] 
            if v["validation_type"] == "id_expiry"
        ]
        assert len(id_expiry_validations) == 1
        assert not id_expiry_validations[0]["is_valid"]

    @patch('backend.api.v1.decisions.get_db')
    def test_evaluate_application_manual_review_mismatch(self, mock_get_db, client, sample_application, sample_mismatched_government_id, test_db):
        """Test application evaluation that results in manual review due to data mismatch."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = sample_application
        test_db.query().filter().all.return_value = [sample_mismatched_government_id]
        
        # Make request
        response = client.post(
            "/api/v1/decisions/evaluate",
            json={"application_id": "test-decision-app-001"}
        )
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert result["decision"] == "manual_review"
        assert result["risk_score"] > 0.3
        
        # Should have failed validations
        failed_validations = [
            v for v in result["validation_results"] 
            if not v["is_valid"]
        ]
        assert len(failed_validations) >= 2  # Name and DOB mismatches

    @patch('backend.api.v1.decisions.get_db')
    def test_evaluate_application_not_found(self, mock_get_db, client, test_db):
        """Test evaluation with invalid application ID."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = None
        
        # Make request
        response = client.post(
            "/api/v1/decisions/evaluate",
            json={"application_id": "invalid-app-id"}
        )
        
        # Verify response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch('backend.api.v1.decisions.get_db')
    def test_evaluate_application_no_documents(self, mock_get_db, client, sample_application, test_db):
        """Test evaluation with application that has no processed documents."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = sample_application
        test_db.query().filter().all.return_value = []  # No documents
        
        # Make request
        response = client.post(
            "/api/v1/decisions/evaluate",
            json={"application_id": "test-decision-app-001"}
        )
        
        # Verify response - should still work but with limited data
        assert response.status_code == 200
        result = response.json()
        assert result["decision"] == "manual_review"  # Default to manual review without documents

    @patch('backend.api.v1.decisions.get_db')
    def test_evaluate_application_with_employer_document(self, mock_get_db, client, sample_application, sample_valid_government_id, test_db):
        """Test evaluation with both government ID and employer document."""
        # Create employer document
        employer_doc = Document(
            id="test-employer-doc-001",
            application_id=sample_application.id,
            document_type=DocumentType.EMPLOYER_DOCUMENT.value,
            file_name="paystub.pdf",
            file_path="/uploads/paystub.pdf",
            content_type="application/pdf",
            file_size=54321,
            processing_status=ProcessingStatus.COMPLETED.value,
            extracted_data={
                "document_type": "pay stub",
                "employee_name": "John Doe",
                "employer_name": "Acme Corporation",
                "document_date": "2023-11-15"
            },
            confidence_scores={
                "employee_name": 0.95,
                "employer_name": 0.95
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = sample_application
        test_db.query().filter().all.return_value = [sample_valid_government_id, employer_doc]
        
        # Make request
        response = client.post(
            "/api/v1/decisions/evaluate",
            json={"application_id": "test-decision-app-001"}
        )
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert result["decision"] == "approve"
        
        # Should include employer validation
        employer_validations = [
            v for v in result["validation_results"] 
            if v["validation_type"] == "employer_match"
        ]
        assert len(employer_validations) == 1
        assert employer_validations[0]["is_valid"]


class TestDecisionStatusAPI:
    """Test cases for decision status endpoints."""

    @patch('backend.api.v1.decisions.get_db')
    def test_get_application_decision_not_implemented(self, mock_get_db, client, test_db):
        """Test getting decision status (currently not implemented)."""
        # Setup mocks
        mock_get_db.return_value = test_db
        
        # Make request
        response = client.get("/api/v1/decisions/test-app-id")
        
        # Verify response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestAuditTrailAPI:
    """Test cases for audit trail endpoint."""

    @patch('backend.api.v1.decisions.get_db')
    def test_get_audit_trail_success(self, mock_get_db, client, sample_application, test_db):
        """Test successful audit trail retrieval."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = sample_application
        
        # Make request
        response = client.get(f"/api/v1/decisions/audit/{sample_application.id}")
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert result["application_id"] == sample_application.id
        assert "entries" in result
        assert "created_at" in result
        assert "updated_at" in result

    @patch('backend.api.v1.decisions.get_db')
    def test_get_audit_trail_application_not_found(self, mock_get_db, client, test_db):
        """Test audit trail retrieval with invalid application ID."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = None
        
        # Make request
        response = client.get("/api/v1/decisions/audit/invalid-app-id")
        
        # Verify response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestDecisionConfigAPI:
    """Test cases for decision configuration endpoints."""

    def test_get_decision_config(self, client):
        """Test getting current decision configuration."""
        response = client.get("/api/v1/decisions/config")
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert "name_match_threshold" in result
        assert "auto_approve_threshold" in result
        assert "manual_review_threshold" in result
        assert "expired_id_auto_reject" in result
        assert result["name_match_threshold"] == 0.7
        assert result["auto_approve_threshold"] == 0.1
        assert result["manual_review_threshold"] == 0.3
        assert result["expired_id_auto_reject"] is True

    def test_update_decision_config(self, client):
        """Test updating decision configuration."""
        new_config = {
            "name_match_threshold": 0.8,
            "auto_approve_threshold": 0.05,
            "manual_review_threshold": 0.2,
            "expired_id_auto_reject": False
        }
        
        response = client.post("/api/v1/decisions/config", json=new_config)
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        assert result["name_match_threshold"] == 0.8
        assert result["auto_approve_threshold"] == 0.05
        assert result["manual_review_threshold"] == 0.2
        assert result["expired_id_auto_reject"] is False

    def test_update_decision_config_invalid_values(self, client):
        """Test updating configuration with invalid values."""
        invalid_config = {
            "name_match_threshold": 1.5,  # Invalid: > 1.0
            "auto_approve_threshold": -0.1,  # Invalid: < 0.0
            "manual_review_threshold": 0.2,
            "expired_id_auto_reject": True
        }
        
        response = client.post("/api/v1/decisions/config", json=invalid_config)
        
        # Verify response
        assert response.status_code == 422  # Validation error


class TestDecisionWorkflowIntegration:
    """Integration tests for complete decision workflow."""

    @patch('backend.api.v1.decisions.get_db')
    def test_complete_decision_workflow(self, mock_get_db, client, sample_application, sample_valid_government_id, test_db):
        """Test complete workflow: evaluate → get config → update config → re-evaluate."""
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = sample_application
        test_db.query().filter().all.return_value = [sample_valid_government_id]
        
        # Step 1: Initial evaluation
        response1 = client.post(
            "/api/v1/decisions/evaluate",
            json={"application_id": "test-decision-app-001"}
        )
        assert response1.status_code == 200
        result1 = response1.json()
        assert result1["decision"] == "approve"
        
        # Step 2: Get current config
        response2 = client.get("/api/v1/decisions/config")
        assert response2.status_code == 200
        config = response2.json()
        
        # Step 3: Update config to be more strict
        strict_config = {
            "name_match_threshold": 0.95,  # Very strict
            "auto_approve_threshold": 0.01,  # Almost no auto-approval
            "manual_review_threshold": 0.05,  # Lower manual review threshold
            "expired_id_auto_reject": True
        }
        response3 = client.post("/api/v1/decisions/config", json=strict_config)
        assert response3.status_code == 200
        
        # Step 4: Re-evaluate with stricter rules
        # (In practice, this might change the outcome depending on confidence scores)
        response4 = client.post(
            "/api/v1/decisions/evaluate",
            json={"application_id": "test-decision-app-001"}
        )
        assert response4.status_code == 200
        result4 = response4.json()
        # Result might be different due to stricter thresholds
        assert result4["decision"] in ["approve", "manual_review"]

    @patch('backend.api.v1.decisions.get_db')
    def test_decision_with_processing_errors(self, mock_get_db, client, sample_application, test_db):
        """Test decision evaluation when document processing fails."""
        # Create document with failed processing
        failed_doc = Document(
            id="test-failed-doc",
            application_id=sample_application.id,
            document_type=DocumentType.GOVERNMENT_ID.value,
            file_name="failed_id.jpg",
            file_path="/uploads/failed_id.jpg",
            content_type="image/jpeg",
            file_size=12345,
            processing_status=ProcessingStatus.FAILED.value,
            processing_error="OCR processing failed",
            extracted_data=None,
            confidence_scores=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = sample_application
        test_db.query().filter().all.return_value = [failed_doc]
        
        # Make request
        response = client.post(
            "/api/v1/decisions/evaluate",
            json={"application_id": "test-decision-app-001"}
        )
        
        # Verify response - should handle gracefully
        assert response.status_code == 200
        result = response.json()
        assert result["decision"] == "manual_review"  # Default to manual review
        assert result["risk_score"] == 0.0  # No risk factors from failed processing


class TestDecisionValidationScenarios:
    """Test specific validation scenarios and edge cases."""

    @patch('backend.api.v1.decisions.get_db')
    def test_boundary_expiry_date(self, mock_get_db, client, sample_application, test_db):
        """Test ID expiring today (boundary condition)."""
        # Create ID expiring today
        today_expiry_id = Document(
            id="test-today-expiry",
            application_id=sample_application.id,
            document_type=DocumentType.GOVERNMENT_ID.value,
            file_name="today_expiry_id.jpg",
            file_path="/uploads/today_expiry_id.jpg",
            content_type="image/jpeg",
            file_size=12345,
            processing_status=ProcessingStatus.COMPLETED.value,
            extracted_data={
                "document_type": "driver's license",
                "id_number": "D1111111",
                "full_name": "John Doe",
                "date_of_birth": "1990-01-15",
                "expiry_date": date.today().strftime("%Y-%m-%d"),  # Expires today
                "issuing_authority": "Department of Motor Vehicles"
            },
            confidence_scores={
                "full_name": 0.95,
                "date_of_birth": 0.90,
                "expiry_date": 0.95
            }
        )
        
        # Setup mocks
        mock_get_db.return_value = test_db
        test_db.query().filter().first.return_value = sample_application
        test_db.query().filter().all.return_value = [today_expiry_id]
        
        # Make request
        response = client.post(
            "/api/v1/decisions/evaluate",
            json={"application_id": "test-decision-app-001"}
        )
        
        # Verify response - ID expiring today should be valid
        assert response.status_code == 200
        result = response.json()
        assert result["decision"] in ["approve", "manual_review"]  # Not rejected
        
        # ID expiry validation should pass
        expiry_validations = [
            v for v in result["validation_results"] 
            if v["validation_type"] == "id_expiry"
        ]
        assert len(expiry_validations) == 1
        assert expiry_validations[0]["is_valid"]

    @patch('backend.api.v1.decisions.get_db')
    def test_partial_name_match_scenarios(self, mock_get_db, client, sample_application, test_db):
        """Test various partial name matching scenarios."""
        test_cases = [
            ("John A. Doe", "John Doe", True),  # Middle initial
            ("John Doe Jr.", "John Doe", True),  # Suffix
            ("J. Doe", "John Doe", False),  # Too abbreviated
            ("John Smith", "Jane Doe", False),  # Completely different
        ]
        
        for app_name, doc_name, should_match in test_cases:
            # Update application name for this test case
            test_application = Application(
                id=sample_application.id,
                full_name=app_name,
                date_of_birth=sample_application.date_of_birth,
                address_street=sample_application.address_street,
                address_city=sample_application.address_city,
                address_state=sample_application.address_state,
                address_zip=sample_application.address_zip,
                social_security_number=sample_application.social_security_number,
                employer_name=sample_application.employer_name,
                status=sample_application.status,
                created_at=sample_application.created_at,
                updated_at=sample_application.updated_at
            )
            
            # Create matching document
            partial_name_id = Document(
                id=f"test-partial-name-{app_name.replace(' ', '-')}",
                application_id=sample_application.id,
                document_type=DocumentType.GOVERNMENT_ID.value,
                file_name="partial_name_id.jpg",
                file_path="/uploads/partial_name_id.jpg",
                content_type="image/jpeg",
                file_size=12345,
                processing_status=ProcessingStatus.COMPLETED.value,
                extracted_data={
                    "document_type": "driver's license",
                    "id_number": "D2222222",
                    "full_name": doc_name,
                    "date_of_birth": "1990-01-15",
                    "expiry_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d"),
                    "issuing_authority": "Department of Motor Vehicles"
                },
                confidence_scores={
                    "full_name": 0.95,
                    "date_of_birth": 0.90,
                    "expiry_date": 0.95
                }
            )
            
            # Setup mocks
            mock_get_db.return_value = test_db
            test_db.query().filter().first.return_value = test_application
            test_db.query().filter().all.return_value = [partial_name_id]
            
            # Make request
            response = client.post(
                "/api/v1/decisions/evaluate",
                json={"application_id": "test-decision-app-001"}
            )
            
            # Verify response
            assert response.status_code == 200
            result = response.json()
            
            # Check name validation result
            name_validations = [
                v for v in result["validation_results"] 
                if v["validation_type"] == "name_match"
            ]
            assert len(name_validations) == 1
            
            if should_match:
                # Should approve or manual review, but not reject due to name
                assert result["decision"] in ["approve", "manual_review"]
                assert name_validations[0]["is_valid"]
            else:
                # Should go to manual review due to name mismatch
                assert result["decision"] == "manual_review"
                assert not name_validations[0]["is_valid"]
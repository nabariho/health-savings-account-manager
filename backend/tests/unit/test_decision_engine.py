"""
Unit tests for decision engine service.

Tests the automated decision-making functionality including business rules,
risk assessment, and validation logic as specified in user stories.

Business Rules Tested:
- Expired ID → Reject  
- Data mismatches → Manual Review
- All valid criteria met → Approve
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime, timedelta
from typing import Dict, Any

from backend.services.decision_engine import DecisionEngine, DecisionEngineError, AuditService
from backend.schemas.decision import (
    DecisionType, ValidationType, ValidationResult, DecisionResult, 
    ApplicationData, DecisionConfig
)


class TestDecisionEngine:
    """Test cases for DecisionEngine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = DecisionConfig(
            name_match_threshold=0.7,
            auto_approve_threshold=0.1,
            manual_review_threshold=0.3,
            expired_id_auto_reject=True
        )
        self.engine = DecisionEngine(self.config)

    @pytest.fixture
    def valid_application_data(self):
        """Valid application data for testing."""
        return ApplicationData(
            application_id="test-app-001",
            full_name="John Doe",
            date_of_birth="1990-01-15",
            address_street="123 Main Street",
            address_city="Anytown",
            address_state="CA",
            address_zip="12345",
            social_security_number="123-45-6789",
            employer_name="Acme Corporation",
            government_id_data={
                "document_type": "driver's license",
                "id_number": "D1234567",
                "full_name": "John Doe",
                "date_of_birth": "1990-01-15",
                "address_street": "123 Main Street",
                "address_city": "Anytown",
                "address_state": "CA",
                "address_zip": "12345",
                "issue_date": "2020-01-15",
                "expiry_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d"),  # Valid for 1 year
                "issuing_authority": "Department of Motor Vehicles"
            }
        )

    @pytest.fixture
    def expired_id_application_data(self):
        """Application data with expired government ID."""
        return ApplicationData(
            application_id="test-app-002",
            full_name="Jane Smith",
            date_of_birth="1985-06-20",
            address_street="456 Oak Avenue",
            address_city="Another City",
            address_state="NY",
            address_zip="67890",
            social_security_number="987-65-4321",
            employer_name="Tech Company Inc",
            government_id_data={
                "document_type": "driver's license",
                "id_number": "NY987654",
                "full_name": "Jane Smith",
                "date_of_birth": "1985-06-20",
                "address_street": "456 Oak Avenue",
                "address_city": "Another City",
                "address_state": "NY",
                "address_zip": "67890",
                "issue_date": "2015-06-20",
                "expiry_date": (date.today() - timedelta(days=30)).strftime("%Y-%m-%d"),  # Expired 30 days ago
                "issuing_authority": "New York Department of Motor Vehicles"
            }
        )

    @pytest.fixture
    def mismatched_data_application(self):
        """Application data with mismatched information."""
        return ApplicationData(
            application_id="test-app-003",
            full_name="Robert Johnson",
            date_of_birth="1988-03-10",
            address_street="789 Pine Road",
            address_city="Somewhere",
            address_state="TX",
            address_zip="13579",
            social_security_number="555-44-3333",
            employer_name="Big Corp LLC",
            government_id_data={
                "document_type": "driver's license",
                "id_number": "TX555444",
                "full_name": "Bob Johnson",  # Name mismatch
                "date_of_birth": "1988-08-10",  # DOB mismatch
                "address_street": "789 Pine Road",
                "address_city": "Somewhere",
                "address_state": "TX",
                "address_zip": "13579",
                "issue_date": "2020-03-10",
                "expiry_date": (date.today() + timedelta(days=180)).strftime("%Y-%m-%d"),
                "issuing_authority": "Texas Department of Public Safety"
            }
        )


class TestBusinessRulesExpiredID:
    """Test expired ID rejection rule (US-3.1: Expired ID → Reject)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = DecisionEngine()

    @pytest.mark.asyncio
    async def test_expired_id_auto_reject(self, expired_id_application_data):
        """Test that expired government ID results in automatic rejection."""
        result = await self.engine.evaluate_application(expired_id_application_data)
        
        assert result.decision == DecisionType.REJECT
        assert result.risk_score == 1.0  # Maximum risk for expired ID
        assert "expired" in result.reasoning.lower()
        
        # Check that ID expiry validation failed
        expiry_validations = [
            v for v in result.validation_results 
            if v.validation_type == ValidationType.ID_EXPIRY
        ]
        assert len(expiry_validations) == 1
        assert not expiry_validations[0].is_valid

    @pytest.mark.asyncio
    async def test_expired_id_with_disabled_auto_reject(self, expired_id_application_data):
        """Test expired ID with auto-reject disabled goes to manual review."""
        config = DecisionConfig(expired_id_auto_reject=False)
        engine = DecisionEngine(config)
        
        result = await engine.evaluate_application(expired_id_application_data)
        
        # Should go to manual review instead of reject when auto-reject disabled
        assert result.decision == DecisionType.MANUAL_REVIEW
        assert result.risk_score > 0.5

    @pytest.mark.asyncio
    async def test_missing_expiry_date_manual_review(self):
        """Test that missing expiry date results in manual review."""
        app_data = ApplicationData(
            application_id="test-no-expiry",
            full_name="Test User",
            date_of_birth="1990-01-01",
            address_street="123 Test St",
            address_city="Test City", 
            address_state="CA",
            address_zip="12345",
            social_security_number="123-45-6789",
            employer_name="Test Co",
            government_id_data={
                "document_type": "passport",
                "id_number": "P123456789",
                "full_name": "Test User",
                "date_of_birth": "1990-01-01"
                # Missing expiry_date
            }
        )
        
        result = await self.engine.evaluate_application(app_data)
        
        assert result.decision == DecisionType.MANUAL_REVIEW
        
        # Check expiry validation marked as invalid
        expiry_validations = [
            v for v in result.validation_results 
            if v.validation_type == ValidationType.ID_EXPIRY
        ]
        assert len(expiry_validations) == 1
        assert not expiry_validations[0].is_valid
        assert "no expiry date" in expiry_validations[0].details.lower()

    @pytest.mark.asyncio 
    async def test_valid_id_expiry_passes(self, valid_application_data):
        """Test that valid (non-expired) ID passes expiry check."""
        result = await self.engine.evaluate_application(valid_application_data)
        
        # Should not be rejected due to expiry
        assert result.decision != DecisionType.REJECT
        
        # Check expiry validation passed
        expiry_validations = [
            v for v in result.validation_results 
            if v.validation_type == ValidationType.ID_EXPIRY
        ]
        assert len(expiry_validations) == 1
        assert expiry_validations[0].is_valid
        assert expiry_validations[0].confidence == 1.0


class TestBusinessRulesDataMismatch:
    """Test data mismatch manual review rule (US-3.1: Mismatch → Manual Review)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = DecisionEngine()

    @pytest.mark.asyncio
    async def test_name_mismatch_manual_review(self):
        """Test that name mismatches result in manual review."""
        app_data = ApplicationData(
            application_id="test-name-mismatch",
            full_name="John Doe",
            date_of_birth="1990-01-15",
            address_street="123 Main St",
            address_city="Test City",
            address_state="CA", 
            address_zip="12345",
            social_security_number="123-45-6789",
            employer_name="Test Corp",
            government_id_data={
                "document_type": "driver's license",
                "id_number": "D1234567", 
                "full_name": "Jane Smith",  # Different name
                "date_of_birth": "1990-01-15",
                "expiry_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
            }
        )
        
        result = await self.engine.evaluate_application(app_data)
        
        assert result.decision == DecisionType.MANUAL_REVIEW
        assert result.risk_score > 0.3
        
        # Check name validation failed
        name_validations = [
            v for v in result.validation_results 
            if v.validation_type == ValidationType.NAME_MATCH
        ]
        assert len(name_validations) == 1
        assert not name_validations[0].is_valid

    @pytest.mark.asyncio
    async def test_dob_mismatch_manual_review(self):
        """Test that date of birth mismatches result in manual review."""
        app_data = ApplicationData(
            application_id="test-dob-mismatch",
            full_name="John Doe",
            date_of_birth="1990-01-15",
            address_street="123 Main St",
            address_city="Test City",
            address_state="CA",
            address_zip="12345", 
            social_security_number="123-45-6789",
            employer_name="Test Corp",
            government_id_data={
                "document_type": "driver's license",
                "id_number": "D1234567",
                "full_name": "John Doe",
                "date_of_birth": "1985-05-20",  # Different DOB
                "expiry_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
            }
        )
        
        result = await self.engine.evaluate_application(app_data)
        
        assert result.decision == DecisionType.MANUAL_REVIEW
        assert result.risk_score > 0.3
        
        # Check DOB validation failed
        dob_validations = [
            v for v in result.validation_results 
            if v.validation_type == ValidationType.DOB_MATCH
        ]
        assert len(dob_validations) == 1
        assert not dob_validations[0].is_valid

    @pytest.mark.asyncio
    async def test_multiple_mismatches_high_risk(self, mismatched_data_application):
        """Test that multiple data mismatches result in high risk score."""
        result = await self.engine.evaluate_application(mismatched_data_application)
        
        assert result.decision == DecisionType.MANUAL_REVIEW
        assert result.risk_score > 0.5  # High risk due to multiple failures
        
        # Should have multiple failed validations
        failed_validations = [v for v in result.validation_results if not v.is_valid]
        assert len(failed_validations) >= 2

    @pytest.mark.asyncio
    async def test_address_mismatch_moderate_risk(self):
        """Test that address mismatches result in moderate risk increase."""
        app_data = ApplicationData(
            application_id="test-address-mismatch",
            full_name="John Doe",
            date_of_birth="1990-01-15",
            address_street="123 Main Street",
            address_city="Anytown", 
            address_state="CA",
            address_zip="12345",
            social_security_number="123-45-6789",
            employer_name="Test Corp",
            government_id_data={
                "document_type": "driver's license",
                "id_number": "D1234567",
                "full_name": "John Doe",
                "date_of_birth": "1990-01-15",
                "address_street": "456 Different St",  # Different address
                "address_city": "Other City",
                "address_state": "NY",
                "address_zip": "67890",
                "expiry_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
            }
        )
        
        result = await self.engine.evaluate_application(app_data)
        
        assert result.decision == DecisionType.MANUAL_REVIEW
        
        # Check address validation failed
        address_validations = [
            v for v in result.validation_results 
            if v.validation_type == ValidationType.ADDRESS_MATCH
        ]
        assert len(address_validations) == 1
        assert not address_validations[0].is_valid


class TestBusinessRulesValidCriteriaApprove:
    """Test valid criteria approval rule (US-3.1: All valid → Approve)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = DecisionEngine()

    @pytest.mark.asyncio
    async def test_all_valid_criteria_approve(self, valid_application_data):
        """Test that applications meeting all criteria are approved."""
        result = await self.engine.evaluate_application(valid_application_data)
        
        assert result.decision == DecisionType.APPROVE
        assert result.risk_score <= 0.1  # Low risk threshold
        assert "validation checks passed" in result.reasoning.lower()
        
        # All validations should pass
        failed_validations = [v for v in result.validation_results if not v.is_valid]
        assert len(failed_validations) == 0

    @pytest.mark.asyncio
    async def test_fuzzy_name_match_approve(self):
        """Test that fuzzy name matching (middle names, initials) still approves."""
        app_data = ApplicationData(
            application_id="test-fuzzy-name",
            full_name="John A. Doe",
            date_of_birth="1990-01-15",
            address_street="123 Main Street",
            address_city="Anytown",
            address_state="CA",
            address_zip="12345",
            social_security_number="123-45-6789",
            employer_name="Test Corp",
            government_id_data={
                "document_type": "driver's license",
                "id_number": "D1234567",
                "full_name": "John Doe",  # Missing middle initial
                "date_of_birth": "1990-01-15",
                "address_street": "123 Main Street",
                "address_city": "Anytown", 
                "address_state": "CA",
                "address_zip": "12345",
                "expiry_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
            }
        )
        
        result = await self.engine.evaluate_application(app_data)
        
        assert result.decision == DecisionType.APPROVE
        
        # Name validation should pass with high confidence
        name_validations = [
            v for v in result.validation_results 
            if v.validation_type == ValidationType.NAME_MATCH
        ]
        assert len(name_validations) == 1
        assert name_validations[0].is_valid
        assert name_validations[0].confidence >= 0.8

    @pytest.mark.asyncio
    async def test_employer_document_validation_approve(self):
        """Test approval with valid employer document."""
        app_data = ApplicationData(
            application_id="test-employer-doc",
            full_name="John Doe",
            date_of_birth="1990-01-15",
            address_street="123 Main Street",
            address_city="Anytown",
            address_state="CA", 
            address_zip="12345",
            social_security_number="123-45-6789",
            employer_name="Acme Corporation",
            government_id_data={
                "document_type": "driver's license",
                "id_number": "D1234567",
                "full_name": "John Doe",
                "date_of_birth": "1990-01-15",
                "expiry_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
            },
            employer_document_data={
                "document_type": "pay stub",
                "employee_name": "John Doe",
                "employer_name": "Acme Corporation",  # Exact match
                "document_date": "2023-11-15"
            }
        )
        
        result = await self.engine.evaluate_application(app_data)
        
        assert result.decision == DecisionType.APPROVE
        
        # Employer validation should pass
        employer_validations = [
            v for v in result.validation_results 
            if v.validation_type == ValidationType.EMPLOYER_MATCH
        ]
        assert len(employer_validations) == 1
        assert employer_validations[0].is_valid


class TestEdgeCasesAndBoundaryConditions:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = DecisionEngine()

    @pytest.mark.asyncio
    async def test_no_government_id_data(self):
        """Test application with no government ID data."""
        app_data = ApplicationData(
            application_id="test-no-gov-id",
            full_name="John Doe",
            date_of_birth="1990-01-15",
            address_street="123 Main Street",
            address_city="Anytown",
            address_state="CA",
            address_zip="12345", 
            social_security_number="123-45-6789",
            employer_name="Test Corp"
            # No government_id_data provided
        )
        
        result = await self.engine.evaluate_application(app_data)
        
        # Should default to manual review with no ID to validate
        assert result.decision == DecisionType.MANUAL_REVIEW
        assert result.risk_score == 0.0  # No risk factors identified

    @pytest.mark.asyncio
    async def test_boundary_risk_scores(self):
        """Test decision boundaries based on risk scores."""
        config = DecisionConfig(
            auto_approve_threshold=0.1,
            manual_review_threshold=0.3
        )
        engine = DecisionEngine(config)
        
        # Test just below auto-approve threshold
        app_data_low_risk = ApplicationData(
            application_id="test-low-risk",
            full_name="John Doe",
            date_of_birth="1990-01-15", 
            address_street="123 Main Street",
            address_city="Anytown",
            address_state="CA",
            address_zip="12345",
            social_security_number="123-45-6789",
            employer_name="Test Corp",
            government_id_data={
                "document_type": "driver's license",
                "id_number": "D1234567",
                "full_name": "John Doe",
                "date_of_birth": "1990-01-15",
                "expiry_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
            }
        )
        
        result = await engine.evaluate_application(app_data_low_risk)
        assert result.decision == DecisionType.APPROVE
        assert result.risk_score <= 0.1

    @pytest.mark.asyncio
    async def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        app_data = ApplicationData(
            application_id="test-missing-fields",
            full_name="",  # Empty name
            date_of_birth="1990-01-15",
            address_street="123 Main Street", 
            address_city="Anytown",
            address_state="CA",
            address_zip="12345",
            social_security_number="123-45-6789",
            employer_name="Test Corp",
            government_id_data={
                "document_type": "driver's license",
                "id_number": "D1234567",
                "full_name": "John Doe",
                "date_of_birth": "1990-01-15",
                "expiry_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
            }
        )
        
        result = await self.engine.evaluate_application(app_data)
        
        assert result.decision == DecisionType.MANUAL_REVIEW
        
        # Name validation should fail due to missing application name
        name_validations = [
            v for v in result.validation_results 
            if v.validation_type == ValidationType.NAME_MATCH
        ]
        assert len(name_validations) == 1
        assert not name_validations[0].is_valid

    @pytest.mark.asyncio 
    async def test_error_handling(self):
        """Test error handling for invalid application data."""
        with pytest.raises(DecisionEngineError):
            # Simulate an error by passing None
            await self.engine.evaluate_application(None)


class TestConfigurableRules:
    """Test configurable business rules."""

    def test_custom_thresholds(self):
        """Test decision engine with custom threshold configuration."""
        config = DecisionConfig(
            name_match_threshold=0.9,  # Very strict matching
            auto_approve_threshold=0.05,  # Very low risk only
            manual_review_threshold=0.2,  # Lower manual review threshold
            expired_id_auto_reject=False  # Disabled auto-reject
        )
        
        engine = DecisionEngine(config)
        
        assert engine.config.name_match_threshold == 0.9
        assert engine.config.auto_approve_threshold == 0.05
        assert engine.config.manual_review_threshold == 0.2
        assert not engine.config.expired_id_auto_reject

    def test_default_configuration(self):
        """Test default configuration values."""
        engine = DecisionEngine()
        
        assert engine.config.name_match_threshold == 0.7
        assert engine.config.auto_approve_threshold == 0.1
        assert engine.config.manual_review_threshold == 0.3
        assert engine.config.expired_id_auto_reject is True


class TestAuditService:
    """Test audit service functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.audit_service = AuditService()

    @pytest.mark.asyncio
    async def test_log_decision(self):
        """Test logging decision to audit trail."""
        decision_result = DecisionResult(
            application_id="test-audit",
            decision=DecisionType.APPROVE,
            risk_score=0.05,
            reasoning="All validation checks passed",
            validation_results=[]
        )
        
        app_data = ApplicationData(
            application_id="test-audit",
            full_name="John Doe",
            date_of_birth="1990-01-15",
            address_street="123 Main Street",
            address_city="Anytown",
            address_state="CA",
            address_zip="12345",
            social_security_number="123-45-6789",
            employer_name="Test Corp"
        )
        
        audit_entry = await self.audit_service.log_decision(decision_result, app_data)
        
        assert audit_entry.application_id == "test-audit"
        assert audit_entry.decision == DecisionType.APPROVE
        assert audit_entry.risk_score == 0.05
        assert audit_entry.system_version == "1.0.0"
        assert audit_entry.application_snapshot is not None

    @pytest.mark.asyncio
    async def test_get_audit_trail(self):
        """Test retrieving audit trail."""
        audit_trail = await self.audit_service.get_audit_trail("test-app-id")
        
        assert audit_trail.application_id == "test-app-id"
        assert isinstance(audit_trail.entries, list)
        assert audit_trail.created_at is not None
        assert audit_trail.updated_at is not None


class TestRiskScoring:
    """Test risk scoring algorithm."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = DecisionEngine()

    def test_risk_score_calculation_no_factors(self):
        """Test risk score calculation with no risk factors."""
        risk_factors = []
        risk_score = self.engine._calculate_risk_score(risk_factors)
        
        assert risk_score == 0.0

    def test_risk_score_calculation_single_factor(self):
        """Test risk score calculation with single risk factor."""
        risk_factors = [("expired_id", 1.0)]
        risk_score = self.engine._calculate_risk_score(risk_factors)
        
        assert risk_score == 1.0  # Maximum weight for expired ID

    def test_risk_score_calculation_multiple_factors(self):
        """Test risk score calculation with multiple risk factors."""
        risk_factors = [
            ("name_mismatch", 0.5),  # Weight 0.8
            ("dob_mismatch", 1.0),   # Weight 0.9
            ("address_mismatch", 0.3) # Weight 0.3
        ]
        risk_score = self.engine._calculate_risk_score(risk_factors)
        
        # Weighted average: (0.5*0.8 + 1.0*0.9 + 0.3*0.3) / (0.8 + 0.9 + 0.3)
        expected = (0.4 + 0.9 + 0.09) / (0.8 + 0.9 + 0.3)
        assert abs(risk_score - expected) < 0.001

    def test_risk_score_capped_at_one(self):
        """Test that risk score is capped at 1.0."""
        # Create scenario that would exceed 1.0
        risk_factors = [
            ("expired_id", 1.0),
            ("name_mismatch", 1.0),
            ("dob_mismatch", 1.0)
        ]
        risk_score = self.engine._calculate_risk_score(risk_factors)
        
        assert risk_score <= 1.0


class TestValidationLogic:
    """Test individual validation methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = DecisionEngine()

    def test_name_validation_exact_match(self):
        """Test exact name matching."""
        result = self.engine._validate_name_match("John Doe", "John Doe")
        
        assert result.is_valid is True
        assert result.confidence == 1.0
        assert result.validation_type == ValidationType.NAME_MATCH

    def test_name_validation_fuzzy_match(self):
        """Test fuzzy name matching."""
        result = self.engine._validate_name_match("John A. Doe", "John Doe")
        
        assert result.is_valid is True
        assert result.confidence == 0.85  # Subset match

    def test_name_validation_no_match(self):
        """Test name validation with no match."""
        result = self.engine._validate_name_match("John Doe", "Jane Smith")
        
        assert result.is_valid is False
        assert result.confidence < 0.7

    def test_dob_validation_exact_match(self):
        """Test exact date of birth matching."""
        result = self.engine._validate_dob_match("1990-01-15", "1990-01-15")
        
        assert result.is_valid is True
        assert result.confidence == 1.0

    def test_dob_validation_mismatch(self):
        """Test date of birth mismatch."""
        result = self.engine._validate_dob_match("1990-01-15", "1985-06-20")
        
        assert result.is_valid is False
        assert result.confidence == 0.0

    def test_employer_validation_exact_match(self):
        """Test exact employer matching."""
        result = self.engine._validate_employer_match("Acme Corporation", "Acme Corporation")
        
        assert result.is_valid is True
        assert result.confidence == 1.0

    def test_employer_validation_fuzzy_match(self):
        """Test fuzzy employer matching."""
        result = self.engine._validate_employer_match("Acme Corp.", "Acme Corporation")
        
        assert result.is_valid is True
        assert result.confidence == 0.8  # Partial match
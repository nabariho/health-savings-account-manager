"""
Additional edge case and boundary condition tests for decision engine.

These tests complement the existing decision engine tests with focus on:
- Edge cases and boundary conditions
- Data validation edge scenarios
- Configuration boundary testing
- Error recovery and resilience
- Complex data matching scenarios
"""

import pytest
from unittest.mock import MagicMock
from datetime import date, datetime, timedelta
from typing import Dict, Any

from backend.services.decision_engine import DecisionEngine, DecisionEngineError, AuditService
from backend.schemas.decision import (
    DecisionType, ValidationType, ValidationResult, DecisionResult, 
    ApplicationData, DecisionConfig
)


class TestDecisionEngineEdgeCases:
    """Edge case and boundary condition tests for DecisionEngine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = DecisionEngine()

    @pytest.mark.asyncio
    async def test_id_expiring_at_midnight_today(self):
        """Test ID that expires at midnight today (boundary condition)."""
        today_str = date.today().strftime("%Y-%m-%d")
        
        app_data = ApplicationData(
            application_id="test-midnight-expiry",
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
                "full_name": "John Doe",
                "date_of_birth": "1990-01-15",
                "expiry_date": today_str  # Expires today
            }
        )
        
        result = await self.engine.evaluate_application(app_data)
        
        # ID expiring today should still be valid (>= comparison)
        assert result.decision != DecisionType.REJECT
        
        # Find expiry validation
        expiry_validations = [
            v for v in result.validation_results 
            if v.validation_type == ValidationType.ID_EXPIRY
        ]
        assert len(expiry_validations) == 1
        assert expiry_validations[0].is_valid is True

    @pytest.mark.asyncio
    async def test_id_expired_one_day_ago(self):
        """Test ID that expired exactly one day ago."""
        yesterday_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        app_data = ApplicationData(
            application_id="test-yesterday-expiry",
            full_name="Jane Smith",
            date_of_birth="1985-06-20",
            address_street="456 Oak Ave",
            address_city="Test City",
            address_state="NY",
            address_zip="67890",
            social_security_number="987-65-4321",
            employer_name="Test Corp",
            government_id_data={
                "document_type": "passport",
                "full_name": "Jane Smith",
                "date_of_birth": "1985-06-20",
                "expiry_date": yesterday_str  # Expired yesterday
            }
        )
        
        result = await self.engine.evaluate_application(app_data)
        
        # Should be rejected due to expired ID
        assert result.decision == DecisionType.REJECT
        assert result.risk_score == 1.0
        
        # Find expiry validation
        expiry_validations = [
            v for v in result.validation_results 
            if v.validation_type == ValidationType.ID_EXPIRY
        ]
        assert len(expiry_validations) == 1
        assert expiry_validations[0].is_valid is False

    @pytest.mark.asyncio
    async def test_malformed_expiry_date_formats(self):
        """Test various malformed expiry date formats."""
        test_cases = [
            "2024-13-01",  # Invalid month
            "2024-02-30",  # Invalid day
            "24-12-01",    # Wrong year format
            "12/31/2024",  # Wrong format
            "2024",        # Year only
            "invalid",     # Non-date string
            "",            # Empty string
        ]
        
        for invalid_date in test_cases:
            app_data = ApplicationData(
                application_id=f"test-invalid-date-{invalid_date[:5]}",
                full_name="Test User",
                date_of_birth="1990-01-01",
                address_street="123 Test St",
                address_city="Test City",
                address_state="CA",
                address_zip="12345",
                social_security_number="123-45-6789",
                employer_name="Test Corp",
                government_id_data={
                    "document_type": "driver's license",
                    "full_name": "Test User",
                    "date_of_birth": "1990-01-01",
                    "expiry_date": invalid_date
                }
            )
            
            result = await self.engine.evaluate_application(app_data)
            
            # Should go to manual review for invalid date formats
            assert result.decision == DecisionType.MANUAL_REVIEW
            
            # Find expiry validation
            expiry_validations = [
                v for v in result.validation_results 
                if v.validation_type == ValidationType.ID_EXPIRY
            ]
            assert len(expiry_validations) == 1
            assert expiry_validations[0].is_valid is False
            assert "invalid" in expiry_validations[0].details.lower() or "error" in expiry_validations[0].details.lower()

    @pytest.mark.asyncio
    async def test_extreme_name_variations(self):
        """Test extreme name variation scenarios."""
        test_cases = [
            # (app_name, doc_name, should_match, description)
            ("José María García-López", "Jose Maria Garcia Lopez", True, "Accent and hyphen differences"),
            ("O'Connor", "OConnor", True, "Apostrophe handling"),
            ("van der Berg", "Van Der Berg", True, "Case differences with particles"),
            ("李小明", "Li Xiaoming", False, "Different scripts"),
            ("Jean-Claude Van Damme", "JC Van Damme", False, "Too abbreviated"),
            ("Elizabeth", "Liz", False, "Nickname vs full name"),
            ("Robert Smith Jr.", "Robert Smith Sr.", False, "Different suffixes"),
            ("Mary Jane Watson", "Jane Watson Mary", False, "Name order switched"),
            ("", "John Doe", False, "Empty application name"),
            ("John Doe", "", False, "Empty document name"),
        ]
        
        for app_name, doc_name, should_match, description in test_cases:
            app_data = ApplicationData(
                application_id=f"test-name-{hash(app_name + doc_name) % 1000}",
                full_name=app_name,
                date_of_birth="1990-01-15",
                address_street="123 Main St",
                address_city="Test City",
                address_state="CA",
                address_zip="12345",
                social_security_number="123-45-6789",
                employer_name="Test Corp",
                government_id_data={
                    "document_type": "driver's license",
                    "full_name": doc_name,
                    "date_of_birth": "1990-01-15",
                    "expiry_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
                }
            )
            
            result = await self.engine.evaluate_application(app_data)
            
            # Find name validation
            name_validations = [
                v for v in result.validation_results 
                if v.validation_type == ValidationType.NAME_MATCH
            ]
            
            if name_validations:
                name_validation = name_validations[0]
                if should_match:
                    assert name_validation.is_valid, f"Failed: {description} - Expected match but got mismatch"
                    assert result.decision in [DecisionType.APPROVE, DecisionType.MANUAL_REVIEW]
                else:
                    assert not name_validation.is_valid, f"Failed: {description} - Expected mismatch but got match"
                    assert result.decision == DecisionType.MANUAL_REVIEW

    @pytest.mark.asyncio
    async def test_address_partial_matches(self):
        """Test address partial matching scenarios."""
        base_app_data = {
            "application_id": "test-address-partial",
            "full_name": "John Doe",
            "date_of_birth": "1990-01-15",
            "social_security_number": "123-45-6789",
            "employer_name": "Test Corp",
            "government_id_data": {
                "document_type": "driver's license",
                "full_name": "John Doe",
                "date_of_birth": "1990-01-15",
                "expiry_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
            }
        }
        
        test_cases = [
            # (app_address, doc_address, expected_validity, description)
            (
                ("123 Main Street", "Anytown", "CA", "12345"),
                ("123 Main St", "Anytown", "CA", "12345"),
                True, "Street abbreviation"
            ),
            (
                ("123 Main Street Apt 4", "Anytown", "CA", "12345"),
                ("123 Main Street", "Anytown", "CA", "12345"),
                True, "Apartment number difference"
            ),
            (
                ("123 Main Street", "Anytown", "CA", "12345"),
                ("456 Oak Avenue", "Other City", "NY", "67890"),
                False, "Completely different address"
            ),
            (
                ("123 Main Street", "Anytown", "CA", "12345"),
                ("123 Main Street", "Anytown", "California", "12345"),
                True, "State name vs abbreviation"
            ),
            (
                ("123 Main Street", "Anytown", "CA", "12345-6789"),
                ("123 Main Street", "Anytown", "CA", "12345"),
                True, "ZIP+4 vs 5-digit ZIP"
            )
        ]
        
        for app_addr, doc_addr, expected_valid, description in test_cases:
            app_data = ApplicationData(
                **base_app_data,
                address_street=app_addr[0],
                address_city=app_addr[1],
                address_state=app_addr[2],
                address_zip=app_addr[3]
            )
            app_data.government_id_data.update({
                "address_street": doc_addr[0],
                "address_city": doc_addr[1], 
                "address_state": doc_addr[2],
                "address_zip": doc_addr[3]
            })
            
            result = await self.engine.evaluate_application(app_data)
            
            # Find address validation
            address_validations = [
                v for v in result.validation_results 
                if v.validation_type == ValidationType.ADDRESS_MATCH
            ]
            
            if address_validations:
                address_validation = address_validations[0]
                if expected_valid:
                    assert address_validation.is_valid, f"Failed: {description} - Expected valid address match"
                else:
                    assert not address_validation.is_valid, f"Failed: {description} - Expected invalid address match"

    @pytest.mark.asyncio
    async def test_configuration_boundary_values(self):
        """Test decision engine with boundary configuration values."""
        # Test minimum threshold values
        config_min = DecisionConfig(
            name_match_threshold=0.0,
            auto_approve_threshold=0.0,
            manual_review_threshold=0.0,
            expired_id_auto_reject=False
        )
        engine_min = DecisionEngine(config_min)
        
        # Test maximum threshold values  
        config_max = DecisionConfig(
            name_match_threshold=1.0,
            auto_approve_threshold=1.0,
            manual_review_threshold=1.0,
            expired_id_auto_reject=True
        )
        engine_max = DecisionEngine(config_max)
        
        app_data = ApplicationData(
            application_id="test-config-boundary",
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
                "full_name": "John Doe",
                "date_of_birth": "1990-01-15",
                "expiry_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
            }
        )
        
        # Test with minimum thresholds (should be very permissive)
        result_min = await engine_min.evaluate_application(app_data)
        assert result_min.decision == DecisionType.APPROVE  # Should approve with min thresholds
        
        # Test with maximum thresholds (should be very restrictive)
        result_max = await engine_max.evaluate_application(app_data)
        assert result_max.decision == DecisionType.MANUAL_REVIEW  # Should require manual review with max thresholds

    @pytest.mark.asyncio
    async def test_unicode_and_special_characters(self):
        """Test handling of Unicode characters and special symbols."""
        test_cases = [
            ("François Müller", "François Müller", True, "Accented characters"),
            ("José-María", "José María", True, "Hyphen vs space"),
            ("O'Neill & Associates", "ONeill and Associates", True, "Apostrophe and ampersand"),
            ("李明", "李明", True, "Chinese characters"),
            ("Smith@Company.com", "Smith at Company dot com", False, "Email symbols"),
            ("Test \n\t Name", "Test Name", True, "Whitespace normalization"),
            ("100% Pure Company", "100 Percent Pure Company", True, "Percentage symbol"),
        ]
        
        for app_name, doc_name, should_match, description in test_cases:
            app_data = ApplicationData(
                application_id=f"test-unicode-{hash(description) % 1000}",
                full_name=app_name,
                date_of_birth="1990-01-15",
                address_street="123 Main St",
                address_city="Test City",
                address_state="CA",
                address_zip="12345",
                social_security_number="123-45-6789",
                employer_name="Test Corp",
                government_id_data={
                    "document_type": "driver's license",
                    "full_name": doc_name,
                    "date_of_birth": "1990-01-15",
                    "expiry_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
                }
            )
            
            # This should not raise exceptions even with special characters
            result = await self.engine.evaluate_application(app_data)
            assert isinstance(result, DecisionResult)
            
            # Find name validation
            name_validations = [
                v for v in result.validation_results 
                if v.validation_type == ValidationType.NAME_MATCH
            ]
            
            assert len(name_validations) == 1, f"Failed: {description} - No name validation found"

    @pytest.mark.asyncio
    async def test_very_long_field_values(self):
        """Test handling of very long field values."""
        long_name = "A" * 1000  # Very long name
        long_address = "B" * 500  # Very long address
        
        app_data = ApplicationData(
            application_id="test-long-fields",
            full_name=long_name,
            date_of_birth="1990-01-15",
            address_street=long_address,
            address_city="Test City",
            address_state="CA",
            address_zip="12345",
            social_security_number="123-45-6789",
            employer_name="Test Corp",
            government_id_data={
                "document_type": "driver's license",
                "full_name": long_name,
                "date_of_birth": "1990-01-15",
                "address_street": long_address,
                "address_city": "Test City",
                "address_state": "CA",
                "address_zip": "12345",
                "expiry_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
            }
        )
        
        # Should handle long fields gracefully
        result = await self.engine.evaluate_application(app_data)
        assert isinstance(result, DecisionResult)
        assert result.reasoning is not None
        assert len(result.validation_results) > 0

    @pytest.mark.asyncio
    async def test_employer_name_edge_cases(self):
        """Test employer name matching edge cases."""
        test_cases = [
            ("Google Inc.", "Google Incorporated", True, "Inc vs Incorporated"),
            ("Apple Corp.", "Apple Corporation", True, "Corp vs Corporation"),
            ("Microsoft LLC", "Microsoft L.L.C.", True, "LLC formatting"),
            ("IBM", "International Business Machines", False, "Acronym vs full name"),
            ("McDonald's", "McDonalds", True, "Apostrophe handling"),
            ("AT&T", "AT and T", True, "Ampersand handling"),
            ("3M Company", "3M Co", True, "Company vs Co"),
            ("General Motors", "GM", False, "Full name vs abbreviation"),
            ("The Walt Disney Company", "Walt Disney Company", True, "Article differences"),
            ("Procter & Gamble", "P&G", False, "Full name vs initials"),
        ]
        
        for app_employer, doc_employer, should_match, description in test_cases:
            app_data = ApplicationData(
                application_id=f"test-employer-{hash(description) % 1000}",
                full_name="John Doe",
                date_of_birth="1990-01-15",
                address_street="123 Main St",
                address_city="Test City",
                address_state="CA",
                address_zip="12345",
                social_security_number="123-45-6789",
                employer_name=app_employer,
                government_id_data={
                    "document_type": "driver's license",
                    "full_name": "John Doe",
                    "date_of_birth": "1990-01-15",
                    "expiry_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
                },
                employer_document_data={
                    "document_type": "pay_stub",
                    "employee_name": "John Doe",
                    "employer_name": doc_employer,
                    "document_date": "2024-01-15"
                }
            )
            
            result = await self.engine.evaluate_application(app_data)
            
            # Find employer validation
            employer_validations = [
                v for v in result.validation_results 
                if v.validation_type == ValidationType.EMPLOYER_MATCH
            ]
            
            if employer_validations:
                employer_validation = employer_validations[0]
                if should_match:
                    assert employer_validation.is_valid, f"Failed: {description} - Expected match"
                    assert employer_validation.confidence >= 0.5
                else:
                    assert not employer_validation.is_valid, f"Failed: {description} - Expected mismatch"

    @pytest.mark.asyncio
    async def test_multiple_simultaneous_issues(self):
        """Test applications with multiple validation issues."""
        app_data = ApplicationData(
            application_id="test-multiple-issues",
            full_name="John Smith",  # Different name
            date_of_birth="1990-01-15",  # Different DOB
            address_street="123 Main St",  # Different address
            address_city="Anytown",
            address_state="CA",
            address_zip="12345",
            social_security_number="123-45-6789",
            employer_name="Test Corp",
            government_id_data={
                "document_type": "driver's license",
                "full_name": "Jane Doe",  # Name mismatch
                "date_of_birth": "1985-06-20",  # DOB mismatch
                "address_street": "456 Oak Ave",  # Address mismatch
                "address_city": "Other City",
                "address_state": "NY",
                "address_zip": "67890",
                "expiry_date": (date.today() - timedelta(days=5)).strftime("%Y-%m-%d")  # Expired ID
            }
        )
        
        result = await self.engine.evaluate_application(app_data)
        
        # Should be rejected due to expired ID (takes precedence)
        assert result.decision == DecisionType.REJECT
        assert result.risk_score == 1.0
        
        # Should have multiple failed validations
        failed_validations = [v for v in result.validation_results if not v.is_valid]
        assert len(failed_validations) >= 3  # At least name, DOB, and expiry failures
        
        # Verify specific validation types are present
        validation_types = {v.validation_type for v in result.validation_results}
        expected_types = {
            ValidationType.ID_EXPIRY,
            ValidationType.NAME_MATCH,
            ValidationType.DOB_MATCH,
            ValidationType.ADDRESS_MATCH
        }
        assert expected_types.issubset(validation_types)

    @pytest.mark.asyncio
    async def test_risk_score_accumulation(self):
        """Test how risk scores accumulate with multiple issues."""
        # Single minor issue
        app_data_minor = ApplicationData(
            application_id="test-minor-risk",
            full_name="John Doe",
            date_of_birth="1990-01-15",
            address_street="123 Main St",  # Slightly different address
            address_city="Anytown",
            address_state="CA",
            address_zip="12345",
            social_security_number="123-45-6789",
            employer_name="Test Corp",
            government_id_data={
                "document_type": "driver's license",
                "full_name": "John Doe",
                "date_of_birth": "1990-01-15",
                "address_street": "123 Main Street",  # Minor address difference
                "address_city": "Anytown",
                "address_state": "CA",
                "address_zip": "12345",
                "expiry_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
            }
        )
        
        # Multiple major issues
        app_data_major = ApplicationData(
            application_id="test-major-risk",
            full_name="John Doe",
            date_of_birth="1990-01-15",
            address_street="123 Main St",
            address_city="Anytown",
            address_state="CA",
            address_zip="12345",
            social_security_number="123-45-6789",
            employer_name="Test Corp",
            government_id_data={
                "document_type": "driver's license",
                "full_name": "Jane Smith",  # Major name mismatch
                "date_of_birth": "1985-06-20",  # Major DOB mismatch
                "address_street": "456 Different Ave",  # Major address mismatch
                "address_city": "Other City",
                "address_state": "NY",
                "address_zip": "67890",
                "expiry_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
            }
        )
        
        result_minor = await self.engine.evaluate_application(app_data_minor)
        result_major = await self.engine.evaluate_application(app_data_major)
        
        # Major issues should have higher risk score
        assert result_major.risk_score > result_minor.risk_score
        
        # Minor issues might still approve or go to manual review
        assert result_minor.decision in [DecisionType.APPROVE, DecisionType.MANUAL_REVIEW]
        
        # Major issues should go to manual review
        assert result_major.decision == DecisionType.MANUAL_REVIEW

    @pytest.mark.asyncio
    async def test_missing_optional_data_handling(self):
        """Test handling when optional data fields are missing."""
        # Application with minimal government ID data
        app_data = ApplicationData(
            application_id="test-minimal-data",
            full_name="John Doe",
            date_of_birth="1990-01-15",
            address_street="123 Main St",
            address_city="Anytown",
            address_state="CA",
            address_zip="12345",
            social_security_number="123-45-6789",
            employer_name="Test Corp",
            government_id_data={
                "document_type": "passport",
                "full_name": "John Doe",
                "date_of_birth": "1990-01-15",
                "expiry_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
                # Missing address fields, ID number, etc.
            }
        )
        
        result = await self.engine.evaluate_application(app_data)
        
        # Should still process successfully
        assert isinstance(result, DecisionResult)
        assert result.decision is not None
        
        # Should have name and DOB validations at minimum
        validation_types = {v.validation_type for v in result.validation_results}
        assert ValidationType.NAME_MATCH in validation_types
        assert ValidationType.DOB_MATCH in validation_types
        assert ValidationType.ID_EXPIRY in validation_types
        
        # Should not have address validation if address data is missing
        if not any(app_data.government_id_data.get(f"address_{field}") for field in ["street", "city", "state", "zip"]):
            assert ValidationType.ADDRESS_MATCH not in validation_types


class TestAuditServiceEdgeCases:
    """Edge case tests for AuditService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.audit_service = AuditService()

    @pytest.mark.asyncio
    async def test_audit_with_complex_data_structures(self):
        """Test auditing with complex nested data structures."""
        complex_app_data = ApplicationData(
            application_id="test-complex-audit",
            full_name="Complex Test User",
            date_of_birth="1990-01-15",
            address_street="123 Complex St",
            address_city="Test City",
            address_state="CA",
            address_zip="12345",
            social_security_number="123-45-6789",
            employer_name="Complex Corp",
            government_id_data={
                "document_type": "driver's license",
                "full_name": "Complex Test User",
                "date_of_birth": "1990-01-15",
                "nested_data": {
                    "issuing_authority": "CA DMV",
                    "restrictions": ["CORRECTIVE LENSES"],
                    "endorsements": []
                },
                "metadata": {
                    "processing_confidence": 0.95,
                    "extraction_model": "gpt-4o",
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            }
        )
        
        complex_decision = DecisionResult(
            application_id="test-complex-audit",
            decision=DecisionType.APPROVE,
            risk_score=0.1,
            reasoning="Complex data processed successfully",
            validation_results=[
                ValidationResult(
                    field_name="complex_validation",
                    validation_type=ValidationType.NAME_MATCH,
                    is_valid=True,
                    confidence=0.95,
                    details="Nested data validation passed"
                )
            ]
        )
        
        # Should handle complex data without errors
        audit_entry = await self.audit_service.log_decision(complex_decision, complex_app_data)
        
        assert audit_entry is not None
        assert audit_entry.application_id == "test-complex-audit"
        assert audit_entry.application_snapshot is not None
        assert isinstance(audit_entry.application_snapshot, dict)

    @pytest.mark.asyncio
    async def test_audit_with_very_large_data(self):
        """Test audit service with very large data structures."""
        # Create large data structures
        large_text = "Large data " * 1000  # Large string
        
        large_app_data = ApplicationData(
            application_id="test-large-audit",
            full_name="Large Data User",
            date_of_birth="1990-01-15",
            address_street="123 Large St",
            address_city="Test City",
            address_state="CA",
            address_zip="12345",
            social_security_number="123-45-6789",
            employer_name="Large Corp",
            government_id_data={
                "document_type": "driver's license",
                "full_name": "Large Data User",
                "date_of_birth": "1990-01-15",
                "large_field": large_text,
                "many_items": list(range(1000))  # Large list
            }
        )
        
        large_decision = DecisionResult(
            application_id="test-large-audit",
            decision=DecisionType.MANUAL_REVIEW,
            risk_score=0.5,
            reasoning=large_text,  # Large reasoning text
            validation_results=[
                ValidationResult(
                    field_name=f"field_{i}",
                    validation_type=ValidationType.NAME_MATCH,
                    is_valid=True,
                    confidence=0.9,
                    details=f"Large validation {i} " * 10
                )
                for i in range(100)  # Many validation results
            ]
        )
        
        # Should handle large data without memory/performance issues
        audit_entry = await self.audit_service.log_decision(large_decision, large_app_data)
        
        assert audit_entry is not None
        assert len(audit_entry.validation_results) == 100
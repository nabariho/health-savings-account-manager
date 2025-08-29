"""
Decision engine for HSA application processing.

This module implements the business logic for automatically evaluating HSA applications
based on document validation, risk assessment, and configurable business rules.

Business Rules (from user stories):
- Expired ID → Reject
- Data mismatches → Manual Review  
- All valid criteria met → Approve
"""

from datetime import date, datetime
from typing import List, Tuple, Dict, Any
import logging

from ..schemas.decision import (
    DecisionType, ValidationType, ValidationResult, DecisionResult, 
    ApplicationData, DecisionConfig, AuditEntry, AuditTrail
)
from ..schemas.document import DocumentType


logger = logging.getLogger(__name__)


class DecisionEngineError(Exception):
    """Exception raised during decision processing."""
    pass


class DecisionEngine:
    """
    HSA application decision engine.
    
    Evaluates applications using business rules and risk scoring to determine
    whether applications should be approved, rejected, or require manual review.
    """
    
    def __init__(self, config: DecisionConfig = None):
        """
        Initialize the decision engine.
        
        Args:
            config: Decision engine configuration. Uses defaults if not provided.
        """
        self.config = config or DecisionConfig()
        self.rules = self._load_decision_rules()
        logger.info(f"Decision engine initialized with config: {self.config}")
    
    def _load_decision_rules(self) -> Dict[str, Any]:
        """Load and validate decision rules configuration."""
        return {
            "expired_id_auto_reject": self.config.expired_id_auto_reject,
            "name_match_threshold": self.config.name_match_threshold,
            "auto_approve_threshold": self.config.auto_approve_threshold,
            "manual_review_threshold": self.config.manual_review_threshold,
        }
    
    async def evaluate_application(self, application_data: ApplicationData) -> DecisionResult:
        """
        Evaluate application using business rules and risk scoring.
        
        Args:
            application_data: Complete application data including extracted documents
            
        Returns:
            DecisionResult: Decision result with reasoning and validation details
            
        Raises:
            DecisionEngineError: If evaluation fails
        """
        try:
            logger.info(f"Evaluating application {application_data.application_id}")
            
            validation_results = []
            risk_factors = []
            
            # Rule 1: Check ID expiry (Expired ID → Reject)
            if application_data.government_id_data:
                expiry_validation = self._check_id_expiry(application_data.government_id_data)
                validation_results.append(expiry_validation)
                
                if not expiry_validation.is_valid and self.config.expired_id_auto_reject:
                    risk_factors.append(("expired_id", 1.0))
            
            # Rule 2: Name matching (Data mismatch → Manual Review)
            if application_data.government_id_data:
                name_validation = self._validate_name_match(
                    application_data.full_name,
                    application_data.government_id_data.get("full_name")
                )
                validation_results.append(name_validation)
                
                if not name_validation.is_valid:
                    risk_factors.append(("name_mismatch", 1.0 - name_validation.confidence))
            
            # Rule 3: Date of birth matching (Data mismatch → Manual Review)
            if application_data.government_id_data:
                dob_validation = self._validate_dob_match(
                    application_data.date_of_birth,
                    application_data.government_id_data.get("date_of_birth")
                )
                validation_results.append(dob_validation)
                
                if not dob_validation.is_valid:
                    risk_factors.append(("dob_mismatch", 1.0))
            
            # Rule 4: Address validation (if available)
            if application_data.government_id_data and self._has_address_data(application_data.government_id_data):
                address_validation = self._validate_address_match(application_data)
                validation_results.append(address_validation)
                
                if not address_validation.is_valid:
                    risk_factors.append(("address_mismatch", 1.0 - address_validation.confidence))
            
            # Rule 5: Employer validation (if employer document available)
            if application_data.employer_document_data:
                employer_validation = self._validate_employer_match(
                    application_data.employer_name,
                    application_data.employer_document_data.get("employer_name")
                )
                validation_results.append(employer_validation)
                
                if not employer_validation.is_valid:
                    risk_factors.append(("employer_mismatch", 1.0 - employer_validation.confidence))
            
            # Calculate final risk score
            risk_score = self._calculate_risk_score(risk_factors)
            
            # Make decision based on business rules
            decision = self._make_decision(validation_results, risk_score)
            reasoning = self._generate_reasoning(validation_results, risk_factors, decision)
            
            result = DecisionResult(
                application_id=application_data.application_id,
                decision=decision,
                risk_score=risk_score,
                reasoning=reasoning,
                validation_results=validation_results
            )
            
            logger.info(f"Decision for {application_data.application_id}: {decision.value} (risk: {risk_score:.3f})")
            return result
            
        except Exception as e:
            logger.error(f"Decision evaluation failed for {application_data.application_id}: {str(e)}")
            raise DecisionEngineError(f"Failed to evaluate application: {str(e)}")
    
    def _check_id_expiry(self, government_id_data: Dict[str, Any]) -> ValidationResult:
        """Check if government ID is expired."""
        expiry_date_str = government_id_data.get("expiry_date")
        
        if not expiry_date_str:
            return ValidationResult(
                field_name="id_expiry",
                validation_type=ValidationType.ID_EXPIRY,
                is_valid=False,
                confidence=0.0,
                details="No expiry date found on ID"
            )
        
        try:
            if isinstance(expiry_date_str, str):
                expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
            else:
                expiry_date = expiry_date_str
            
            today = date.today()
            is_valid = expiry_date >= today
            
            return ValidationResult(
                field_name="id_expiry",
                validation_type=ValidationType.ID_EXPIRY,
                is_valid=is_valid,
                confidence=1.0,
                details=f"ID expires on {expiry_date}. Current date: {today}",
                document_value=str(expiry_date)
            )
            
        except Exception as e:
            return ValidationResult(
                field_name="id_expiry",
                validation_type=ValidationType.ID_EXPIRY,
                is_valid=False,
                confidence=0.0,
                details=f"Invalid expiry date format: {str(e)}"
            )
    
    def _validate_name_match(self, app_name: str, doc_name: str) -> ValidationResult:
        """Validate name matching with fuzzy logic."""
        if not app_name or not doc_name:
            return ValidationResult(
                field_name="full_name",
                validation_type=ValidationType.NAME_MATCH,
                is_valid=False,
                confidence=0.0,
                details="Missing name data",
                application_value=app_name,
                document_value=doc_name
            )
        
        # Clean names for comparison
        app_clean = app_name.lower().replace(",", "").replace(".", "").strip()
        doc_clean = doc_name.lower().replace(",", "").replace(".", "").strip()
        
        if app_clean == doc_clean:
            confidence = 1.0
            is_valid = True
            details = "Exact match"
        else:
            # Check subset matching (handles middle names, initials)
            app_words = set(app_clean.split())
            doc_words = set(doc_clean.split())
            
            if app_words.issubset(doc_words) or doc_words.issubset(app_words):
                confidence = 0.85
                is_valid = confidence >= self.config.name_match_threshold
                details = "Subset match (middle name/initial variation)"
            else:
                # Basic character similarity
                common_chars = set(app_clean) & set(doc_clean)
                similarity = len(common_chars) / max(len(app_clean), len(doc_clean))
                confidence = min(similarity, 0.8)  # Cap at 0.8 for character matching
                is_valid = confidence >= self.config.name_match_threshold
                details = f"Character similarity: {similarity:.2f}"
        
        return ValidationResult(
            field_name="full_name",
            validation_type=ValidationType.NAME_MATCH,
            is_valid=is_valid,
            confidence=confidence,
            details=details,
            application_value=app_name,
            document_value=doc_name
        )
    
    def _validate_dob_match(self, app_dob: str, doc_dob: str) -> ValidationResult:
        """Validate date of birth exact matching."""
        if not app_dob or not doc_dob:
            return ValidationResult(
                field_name="date_of_birth",
                validation_type=ValidationType.DOB_MATCH,
                is_valid=False,
                confidence=0.0,
                details="Missing date of birth data",
                application_value=app_dob,
                document_value=doc_dob
            )
        
        try:
            # Normalize date formats for comparison
            app_date = str(app_dob).strip()
            doc_date = str(doc_dob).strip()
            
            is_valid = app_date == doc_date
            confidence = 1.0 if is_valid else 0.0
            details = "Exact match" if is_valid else "Date of birth mismatch"
            
            return ValidationResult(
                field_name="date_of_birth",
                validation_type=ValidationType.DOB_MATCH,
                is_valid=is_valid,
                confidence=confidence,
                details=details,
                application_value=app_date,
                document_value=doc_date
            )
            
        except Exception as e:
            return ValidationResult(
                field_name="date_of_birth",
                validation_type=ValidationType.DOB_MATCH,
                is_valid=False,
                confidence=0.0,
                details=f"Date validation error: {str(e)}",
                application_value=app_dob,
                document_value=doc_dob
            )
    
    def _has_address_data(self, government_id_data: Dict[str, Any]) -> bool:
        """Check if government ID has address information."""
        address_fields = ["address_street", "address_city", "address_state", "address_zip"]
        return any(government_id_data.get(field) for field in address_fields)
    
    def _validate_address_match(self, application_data: ApplicationData) -> ValidationResult:
        """Validate address matching with fuzzy logic."""
        gov_id = application_data.government_id_data
        
        # Extract address components
        doc_street = gov_id.get("address_street", "").lower()
        doc_city = gov_id.get("address_city", "").lower()
        doc_state = gov_id.get("address_state", "").lower()
        doc_zip = gov_id.get("address_zip", "").lower()
        
        app_street = application_data.address_street.lower()
        app_city = application_data.address_city.lower()
        app_state = application_data.address_state.lower()
        app_zip = application_data.address_zip.lower()
        
        # Calculate component matches
        matches = []
        if doc_street and app_street:
            matches.append(1.0 if doc_street in app_street or app_street in doc_street else 0.0)
        if doc_city and app_city:
            matches.append(1.0 if doc_city == app_city else 0.0)
        if doc_state and app_state:
            matches.append(1.0 if doc_state == app_state else 0.0)
        if doc_zip and app_zip:
            matches.append(1.0 if doc_zip == app_zip else 0.0)
        
        if not matches:
            confidence = 0.0
            is_valid = False
            details = "No address components could be compared"
        else:
            confidence = sum(matches) / len(matches)
            is_valid = confidence > 0.5
            details = f"Address component match score: {confidence:.2f}"
        
        doc_address = f"{doc_street} {doc_city} {doc_state} {doc_zip}".strip()
        app_address = f"{app_street} {app_city} {app_state} {app_zip}".strip()
        
        return ValidationResult(
            field_name="address",
            validation_type=ValidationType.ADDRESS_MATCH,
            is_valid=is_valid,
            confidence=confidence,
            details=details,
            application_value=app_address,
            document_value=doc_address
        )
    
    def _validate_employer_match(self, app_employer: str, doc_employer: str) -> ValidationResult:
        """Validate employer name matching with fuzzy logic."""
        if not app_employer or not doc_employer:
            return ValidationResult(
                field_name="employer_name",
                validation_type=ValidationType.EMPLOYER_MATCH,
                is_valid=False,
                confidence=0.0,
                details="Missing employer data",
                application_value=app_employer,
                document_value=doc_employer
            )
        
        # Clean employer names (remove common suffixes)
        app_clean = app_employer.lower().replace("inc.", "").replace("corp.", "").replace("llc", "").strip()
        doc_clean = doc_employer.lower().replace("inc.", "").replace("corp.", "").replace("llc", "").strip()
        
        if app_clean == doc_clean:
            confidence = 1.0
            is_valid = True
            details = "Exact match"
        elif app_clean in doc_clean or doc_clean in app_clean:
            confidence = 0.8
            is_valid = True
            details = "Partial match (company name variation)"
        else:
            # Check for common words
            app_words = set(app_clean.split())
            doc_words = set(doc_clean.split())
            common_words = app_words & doc_words
            
            if common_words:
                confidence = min(len(common_words) / max(len(app_words), len(doc_words)), 0.7)
                is_valid = confidence > 0.5
                details = f"Common words found: {', '.join(common_words)}"
            else:
                confidence = 0.0
                is_valid = False
                details = "No matching words found"
        
        return ValidationResult(
            field_name="employer_name",
            validation_type=ValidationType.EMPLOYER_MATCH,
            is_valid=is_valid,
            confidence=confidence,
            details=details,
            application_value=app_employer,
            document_value=doc_employer
        )
    
    def _calculate_risk_score(self, risk_factors: List[Tuple[str, float]]) -> float:
        """
        Calculate overall risk score based on validation failures.
        
        Args:
            risk_factors: List of (risk_type, weight) tuples
            
        Returns:
            Risk score between 0.0 (low risk) and 1.0 (high risk)
        """
        if not risk_factors:
            return 0.0
        
        # Weight different risk factors
        risk_weights = {
            "expired_id": 1.0,      # Critical - auto reject
            "name_mismatch": 0.8,   # High risk
            "dob_mismatch": 0.9,    # Very high risk
            "address_mismatch": 0.3, # Medium risk
            "employer_mismatch": 0.4 # Medium risk
        }
        
        total_risk = 0.0
        total_weight = 0.0
        
        for risk_type, factor_score in risk_factors:
            weight = risk_weights.get(risk_type, 0.5)
            total_risk += factor_score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        # Normalize and cap at 1.0
        risk_score = min(total_risk / total_weight, 1.0)
        return risk_score
    
    def _make_decision(self, validations: List[ValidationResult], risk_score: float) -> DecisionType:
        """
        Make final decision based on validation results and risk score.
        
        Business Rules:
        1. Expired ID → Reject
        2. High risk score → Manual Review
        3. Any validation failures → Manual Review
        4. Low risk score + all valid → Approve
        """
        
        # Rule 1: Auto-reject for expired ID
        expired_id = any(
            v.validation_type == ValidationType.ID_EXPIRY and not v.is_valid 
            for v in validations
        )
        if expired_id and self.config.expired_id_auto_reject:
            return DecisionType.REJECT
        
        # Rule 2: Manual review for high risk
        if risk_score >= self.config.manual_review_threshold:
            return DecisionType.MANUAL_REVIEW
        
        # Rule 3: Manual review for any validation failures
        has_failures = any(not v.is_valid for v in validations)
        if has_failures:
            return DecisionType.MANUAL_REVIEW
        
        # Rule 4: Auto-approve for low risk + all valid
        if risk_score <= self.config.auto_approve_threshold:
            return DecisionType.APPROVE
        
        # Default to manual review for edge cases
        return DecisionType.MANUAL_REVIEW
    
    def _generate_reasoning(
        self, 
        validations: List[ValidationResult], 
        risk_factors: List[Tuple[str, float]], 
        decision: DecisionType
    ) -> str:
        """Generate human-readable explanation for the decision."""
        
        reasons = []
        
        if decision == DecisionType.REJECT:
            # Find rejection reasons
            expired_id = any(
                v.validation_type == ValidationType.ID_EXPIRY and not v.is_valid 
                for v in validations
            )
            if expired_id:
                reasons.append("Government ID is expired")
        
        elif decision == DecisionType.MANUAL_REVIEW:
            # Find reasons for manual review
            failed_validations = [v for v in validations if not v.is_valid]
            for validation in failed_validations:
                reasons.append(f"{validation.field_name}: {validation.details}")
            
            if not failed_validations and risk_factors:
                reasons.append("Moderate risk score requires human review")
        
        elif decision == DecisionType.APPROVE:
            reasons.append("All validation checks passed")
            passed_count = len([v for v in validations if v.is_valid])
            if passed_count > 0:
                reasons.append(f"Validated {passed_count} data points successfully")
        
        if not reasons:
            reasons.append("Decision based on configured business rules")
        
        return ". ".join(reasons) + "."


class AuditService:
    """Service for maintaining audit trails of decision history."""
    
    def __init__(self):
        """Initialize the audit service."""
        self.system_version = "1.0.0"  # Would be populated from config
    
    async def log_decision(
        self, 
        decision_result: DecisionResult, 
        application_data: ApplicationData
    ) -> AuditEntry:
        """
        Log a decision to the audit trail.
        
        Args:
            decision_result: The decision that was made
            application_data: Complete application data at time of decision
            
        Returns:
            AuditEntry: The created audit entry
        """
        audit_entry = AuditEntry(
            application_id=decision_result.application_id,
            decision=decision_result.decision,
            risk_score=decision_result.risk_score,
            reasoning=decision_result.reasoning,
            validation_results=decision_result.validation_results,
            application_snapshot=application_data.model_dump(),
            system_version=self.system_version
        )
        
        # In a real implementation, this would persist to database
        logger.info(f"Audit entry created for application {audit_entry.application_id}")
        
        return audit_entry
    
    async def get_audit_trail(self, application_id: str) -> AuditTrail:
        """
        Get complete audit trail for an application.
        
        Args:
            application_id: Application to get audit trail for
            
        Returns:
            AuditTrail: Complete audit history
        """
        # In a real implementation, this would query the database
        # For now, return empty trail
        return AuditTrail(
            application_id=application_id,
            entries=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
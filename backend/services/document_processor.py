"""
Document processing service using OpenAI vision capabilities.

This module provides document processing functionality using GPT-4o
for extracting structured data from government IDs and employer documents.
"""

import json
import base64
import asyncio
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from io import BytesIO
from pathlib import Path

import openai
from openai import OpenAI
from PIL import Image

from ..core.config import settings
from ..schemas.document import (
    DocumentType, 
    GovernmentIdData, 
    EmployerDocumentData,
    ValidationResult
)


class DocumentProcessingError(Exception):
    """Exception raised during document processing."""
    pass


class DocumentProcessor:
    """
    Document processor using OpenAI GPT-4o vision model.
    
    Handles extraction of structured data from government IDs and
    employer documents using computer vision and natural language processing.
    """
    
    def __init__(self):
        """Initialize the document processor."""
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.vision_model = "gpt-4o"
    
    async def process_document(
        self, 
        file_content: bytes, 
        document_type: DocumentType,
        file_name: str
    ) -> Tuple[Dict[str, Any], Dict[str, float]]:
        """
        Process a document and extract structured data.
        
        Args:
            file_content: Binary content of the document
            document_type: Type of document being processed
            file_name: Original filename for context
            
        Returns:
            Tuple of (extracted_data, confidence_scores)
            
        Raises:
            DocumentProcessingError: If processing fails
        """
        try:
            # Validate and prepare image
            image_data = await self._prepare_image(file_content, file_name)
            
            if document_type == DocumentType.GOVERNMENT_ID:
                return await self._process_government_id(image_data)
            elif document_type == DocumentType.EMPLOYER_DOCUMENT:
                return await self._process_employer_document(image_data)
            else:
                raise DocumentProcessingError(f"Unsupported document type: {document_type}")
                
        except Exception as e:
            raise DocumentProcessingError(f"Failed to process document: {str(e)}")
    
    async def _prepare_image(self, file_content: bytes, file_name: str) -> str:
        """
        Prepare image data for OpenAI vision API.
        
        Args:
            file_content: Binary image data
            file_name: Original filename
            
        Returns:
            Base64 encoded image data
            
        Raises:
            DocumentProcessingError: If image preparation fails
        """
        try:
            # Validate file size (max 20MB for OpenAI)
            if len(file_content) > 20 * 1024 * 1024:
                raise DocumentProcessingError("File size exceeds 20MB limit")
            
            # Try to open image to validate format
            try:
                image = Image.open(BytesIO(file_content))
                image.verify()
            except Exception:
                raise DocumentProcessingError("Invalid image format")
            
            # Convert to base64
            image_b64 = base64.b64encode(file_content).decode('utf-8')
            return image_b64
            
        except DocumentProcessingError:
            raise
        except Exception as e:
            raise DocumentProcessingError(f"Failed to prepare image: {str(e)}")
    
    async def _process_government_id(self, image_data: str) -> Tuple[Dict[str, Any], Dict[str, float]]:
        """
        Extract structured data from government ID using GPT-4o vision.
        
        Args:
            image_data: Base64 encoded image data
            
        Returns:
            Tuple of (extracted_data, confidence_scores)
        """
        prompt = """
        Extract the following information from this government-issued ID document:
        
        Required fields:
        - document_type: Type of ID (driver's license, passport, state ID, etc.)
        - id_number: The ID number/license number
        - full_name: Full name as it appears on the document
        - date_of_birth: Date of birth (YYYY-MM-DD format)
        
        Optional fields (if available):
        - address_street: Street address
        - address_city: City
        - address_state: State (2-letter abbreviation)
        - address_zip: ZIP/postal code
        - issue_date: Date issued (YYYY-MM-DD format)
        - expiry_date: Expiry date (YYYY-MM-DD format)
        - issuing_authority: Issuing authority/organization
        
        Return the data as JSON with two objects:
        1. "extracted_data": The extracted information
        2. "confidence_scores": Confidence scores (0.0-1.0) for each extracted field
        
        If a field cannot be determined, omit it from extracted_data and set confidence to 0.0.
        Be conservative with confidence scores - only use high scores (>0.8) for clearly visible text.
        """
        
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url", 
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=1000,
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            extracted_data = result.get("extracted_data", {})
            confidence_scores = result.get("confidence_scores", {})
            
            # Validate the extracted data structure
            if extracted_data:
                gov_id_data = GovernmentIdData.model_validate(extracted_data)
                return gov_id_data.model_dump(), confidence_scores
            else:
                raise DocumentProcessingError("No data could be extracted from the document")
            
        except json.JSONDecodeError as e:
            raise DocumentProcessingError(f"Invalid JSON response from OpenAI: {str(e)}")
        except Exception as e:
            raise DocumentProcessingError(f"Failed to process government ID: {str(e)}")
    
    async def _process_employer_document(self, image_data: str) -> Tuple[Dict[str, Any], Dict[str, float]]:
        """
        Extract structured data from employer document using GPT-4o vision.
        
        Args:
            image_data: Base64 encoded image data
            
        Returns:
            Tuple of (extracted_data, confidence_scores)
        """
        prompt = """
        Extract the following information from this employer document (pay stub, employment letter, etc.):
        
        Required fields:
        - document_type: Type of document (pay stub, employment letter, benefits summary, etc.)
        - employee_name: Employee name as it appears on the document
        - employer_name: Employer/company name
        
        Optional fields (if available):
        - employer_address: Employer address
        - document_date: Date on the document (YYYY-MM-DD format)
        - health_plan_type: Health plan type if mentioned (High Deductible Health Plan, etc.)
        
        Return the data as JSON with two objects:
        1. "extracted_data": The extracted information
        2. "confidence_scores": Confidence scores (0.0-1.0) for each extracted field
        
        If a field cannot be determined, omit it from extracted_data and set confidence to 0.0.
        Be conservative with confidence scores - only use high scores (>0.8) for clearly visible text.
        """
        
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url", 
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            extracted_data = result.get("extracted_data", {})
            confidence_scores = result.get("confidence_scores", {})
            
            # Validate the extracted data structure
            if extracted_data:
                employer_doc_data = EmployerDocumentData.model_validate(extracted_data)
                return employer_doc_data.model_dump(), confidence_scores
            else:
                raise DocumentProcessingError("No data could be extracted from the document")
            
        except json.JSONDecodeError as e:
            raise DocumentProcessingError(f"Invalid JSON response from OpenAI: {str(e)}")
        except Exception as e:
            raise DocumentProcessingError(f"Failed to process employer document: {str(e)}")
    
    def validate_against_application(
        self, 
        extracted_data: Dict[str, Any], 
        application_data: Dict[str, Any],
        document_type: DocumentType
    ) -> Tuple[List[ValidationResult], float]:
        """
        Validate extracted document data against application data.
        
        Args:
            extracted_data: Data extracted from document
            application_data: Application personal information
            document_type: Type of document being validated
            
        Returns:
            Tuple of (validation_results, overall_score)
        """
        validation_results = []
        match_scores = []
        
        if document_type == DocumentType.GOVERNMENT_ID:
            # Validate name
            name_result = self._validate_name(
                extracted_data.get("full_name"),
                application_data.get("full_name")
            )
            validation_results.append(name_result)
            match_scores.append(name_result.confidence_score if name_result.is_match else 0.0)
            
            # Validate date of birth
            dob_result = self._validate_date_of_birth(
                extracted_data.get("date_of_birth"),
                application_data.get("date_of_birth")
            )
            validation_results.append(dob_result)
            match_scores.append(dob_result.confidence_score if dob_result.is_match else 0.0)
            
            # Validate address if available
            if extracted_data.get("address_street"):
                address_result = self._validate_address(extracted_data, application_data)
                validation_results.append(address_result)
                match_scores.append(address_result.confidence_score if address_result.is_match else 0.0)
        
        elif document_type == DocumentType.EMPLOYER_DOCUMENT:
            # Validate employee name
            name_result = self._validate_name(
                extracted_data.get("employee_name"),
                application_data.get("full_name")
            )
            validation_results.append(name_result)
            match_scores.append(name_result.confidence_score if name_result.is_match else 0.0)
            
            # Validate employer name
            employer_result = self._validate_employer(
                extracted_data.get("employer_name"),
                application_data.get("employer_name")
            )
            validation_results.append(employer_result)
            match_scores.append(employer_result.confidence_score if employer_result.is_match else 0.0)
        
        # Calculate overall score
        overall_score = sum(match_scores) / len(match_scores) if match_scores else 0.0
        
        return validation_results, overall_score
    
    def _validate_name(self, doc_name: Optional[str], app_name: Optional[str]) -> ValidationResult:
        """Validate name fields with fuzzy matching."""
        if not doc_name or not app_name:
            return ValidationResult(
                field_name="full_name",
                application_value=app_name,
                document_value=doc_name,
                is_match=False,
                confidence_score=0.0,
                reason="Missing name data"
            )
        
        # Simple fuzzy matching logic (can be enhanced with more sophisticated algorithms)
        doc_name_clean = doc_name.lower().replace(",", "").replace(".", "").strip()
        app_name_clean = app_name.lower().replace(",", "").replace(".", "").strip()
        
        if doc_name_clean == app_name_clean:
            confidence = 1.0
            is_match = True
        else:
            # Check if all words in one name appear in the other
            doc_words = set(doc_name_clean.split())
            app_words = set(app_name_clean.split())
            
            if doc_words.issubset(app_words) or app_words.issubset(doc_words):
                confidence = 0.85
                is_match = True
            else:
                # Basic string similarity
                common_chars = set(doc_name_clean) & set(app_name_clean)
                similarity = len(common_chars) / max(len(doc_name_clean), len(app_name_clean))
                
                if similarity > 0.7:
                    confidence = 0.7
                    is_match = True
                else:
                    confidence = similarity
                    is_match = False
        
        return ValidationResult(
            field_name="full_name",
            application_value=app_name,
            document_value=doc_name,
            is_match=is_match,
            confidence_score=confidence,
            reason="Exact match" if confidence == 1.0 else f"Similarity: {confidence:.2f}"
        )
    
    def _validate_date_of_birth(
        self, 
        doc_dob: Optional[str], 
        app_dob: Optional[str]
    ) -> ValidationResult:
        """Validate date of birth with exact matching."""
        if not doc_dob or not app_dob:
            return ValidationResult(
                field_name="date_of_birth",
                application_value=app_dob,
                document_value=doc_dob,
                is_match=False,
                confidence_score=0.0,
                reason="Missing date of birth data"
            )
        
        # Convert to comparable format
        try:
            if isinstance(doc_dob, str):
                doc_date_str = doc_dob
            else:
                doc_date_str = str(doc_dob)
                
            if isinstance(app_dob, str):
                app_date_str = app_dob
            else:
                app_date_str = str(app_dob)
            
            is_match = doc_date_str == app_date_str
            confidence = 1.0 if is_match else 0.0
            
            return ValidationResult(
                field_name="date_of_birth",
                application_value=app_date_str,
                document_value=doc_date_str,
                is_match=is_match,
                confidence_score=confidence,
                reason="Exact match" if is_match else "Date mismatch"
            )
            
        except Exception:
            return ValidationResult(
                field_name="date_of_birth",
                application_value=app_dob,
                document_value=doc_dob,
                is_match=False,
                confidence_score=0.0,
                reason="Date format error"
            )
    
    def _validate_address(
        self, 
        extracted_data: Dict[str, Any], 
        application_data: Dict[str, Any]
    ) -> ValidationResult:
        """Validate address fields."""
        doc_street = extracted_data.get("address_street", "").lower()
        doc_city = extracted_data.get("address_city", "").lower()
        doc_state = extracted_data.get("address_state", "").lower()
        doc_zip = extracted_data.get("address_zip", "").lower()
        
        app_street = application_data.get("address_street", "").lower()
        app_city = application_data.get("address_city", "").lower()
        app_state = application_data.get("address_state", "").lower()
        app_zip = application_data.get("address_zip", "").lower()
        
        matches = []
        if doc_street and app_street:
            matches.append(doc_street in app_street or app_street in doc_street)
        if doc_city and app_city:
            matches.append(doc_city == app_city)
        if doc_state and app_state:
            matches.append(doc_state == app_state)
        if doc_zip and app_zip:
            matches.append(doc_zip == app_zip)
        
        if not matches:
            confidence = 0.0
            is_match = False
        else:
            confidence = sum(matches) / len(matches)
            is_match = confidence > 0.5
        
        doc_address = f"{doc_street} {doc_city} {doc_state} {doc_zip}".strip()
        app_address = f"{app_street} {app_city} {app_state} {app_zip}".strip()
        
        return ValidationResult(
            field_name="address",
            application_value=app_address,
            document_value=doc_address,
            is_match=is_match,
            confidence_score=confidence,
            reason=f"Address match score: {confidence:.2f}"
        )
    
    def _validate_employer(
        self, 
        doc_employer: Optional[str], 
        app_employer: Optional[str]
    ) -> ValidationResult:
        """Validate employer name with fuzzy matching."""
        if not doc_employer or not app_employer:
            return ValidationResult(
                field_name="employer_name",
                application_value=app_employer,
                document_value=doc_employer,
                is_match=False,
                confidence_score=0.0,
                reason="Missing employer data"
            )
        
        doc_employer_clean = doc_employer.lower().replace("inc.", "").replace("corp.", "").replace("llc", "").strip()
        app_employer_clean = app_employer.lower().replace("inc.", "").replace("corp.", "").replace("llc", "").strip()
        
        if doc_employer_clean == app_employer_clean:
            confidence = 1.0
            is_match = True
        else:
            # Check for partial matches
            if doc_employer_clean in app_employer_clean or app_employer_clean in doc_employer_clean:
                confidence = 0.8
                is_match = True
            else:
                # Basic word matching
                doc_words = set(doc_employer_clean.split())
                app_words = set(app_employer_clean.split())
                
                if doc_words & app_words:  # Any common words
                    confidence = 0.6
                    is_match = True
                else:
                    confidence = 0.0
                    is_match = False
        
        return ValidationResult(
            field_name="employer_name",
            application_value=app_employer,
            document_value=doc_employer,
            is_match=is_match,
            confidence_score=confidence,
            reason="Exact match" if confidence == 1.0 else f"Similarity: {confidence:.2f}"
        )
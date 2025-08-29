/**
 * Type definitions for document processing.
 * 
 * These types match the backend API schemas and provide type safety
 * for document upload and processing functionality.
 */

/**
 * Document type enumeration.
 */
export type DocumentType = 'government_id' | 'employer_document';

/**
 * Processing status enumeration.
 */
export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';

/**
 * Document upload request payload.
 */
export interface DocumentUploadRequest {
  /** Application ID this document belongs to */
  application_id: string;
  /** Type of document being uploaded */
  document_type: DocumentType;
}

/**
 * Extracted government ID data from OCR.
 */
export interface GovernmentIdData {
  /** Type of government ID */
  document_type: string;
  /** ID number from the document */
  id_number: string;
  /** Full name as it appears on the ID */
  full_name: string;
  /** Date of birth from the ID */
  date_of_birth: string;
  /** Street address from the ID */
  address_street?: string;
  /** City from the ID */
  address_city?: string;
  /** State from the ID */
  address_state?: string;
  /** ZIP code from the ID */
  address_zip?: string;
  /** Issue date of the ID */
  issue_date?: string;
  /** Expiry date of the ID */
  expiry_date?: string;
  /** Issuing authority */
  issuing_authority?: string;
}

/**
 * Extracted employer document data from OCR.
 */
export interface EmployerDocumentData {
  /** Type of employer document */
  document_type: string;
  /** Employee name from the document */
  employee_name: string;
  /** Employer name from the document */
  employer_name: string;
  /** Employer address if available */
  employer_address?: string;
  /** Date on the document */
  document_date?: string;
  /** Type of health plan mentioned */
  health_plan_type?: string;
}

/**
 * Document processing response from API.
 */
export interface DocumentProcessingResponse {
  /** Document unique identifier */
  id: string;
  /** Associated application ID */
  application_id: string;
  /** Type of document */
  document_type: DocumentType;
  /** Original filename */
  file_name: string;
  /** MIME type of the file */
  content_type: string;
  /** File size in bytes */
  file_size: number;
  /** Current processing status */
  processing_status: ProcessingStatus;
  /** Extracted data from the document */
  extracted_data?: GovernmentIdData | EmployerDocumentData;
  /** Error message if processing failed */
  processing_error?: string;
  /** Confidence scores for extracted fields */
  confidence_scores?: Record<string, number>;
  /** When the document was uploaded */
  created_at: string;
  /** When the document was last updated */
  updated_at: string;
}

/**
 * Document status response.
 */
export interface DocumentStatusResponse {
  /** Document unique identifier */
  id: string;
  /** Current processing status */
  processing_status: ProcessingStatus;
  /** Extracted data if processing completed */
  extracted_data?: GovernmentIdData | EmployerDocumentData;
  /** Error message if processing failed */
  processing_error?: string;
  /** Confidence scores for extracted fields */
  confidence_scores?: Record<string, number>;
  /** When the document was last updated */
  updated_at: string;
}

/**
 * Validation result for comparing extracted data with application data.
 */
export interface ValidationResult {
  /** Name of the field being validated */
  field_name: string;
  /** Value from the application */
  application_value?: string;
  /** Value extracted from the document */
  document_value?: string;
  /** Whether the values match */
  is_match: boolean;
  /** Confidence score for the match */
  confidence_score: number;
  /** Reason for the validation result */
  reason?: string;
}

/**
 * Document validation response.
 */
export interface DocumentValidationResponse {
  /** Document unique identifier */
  document_id: string;
  /** Associated application ID */
  application_id: string;
  /** Overall match score between document and application data */
  overall_match_score: number;
  /** Individual field validation results */
  validation_results: ValidationResult[];
  /** Recommendation based on validation */
  recommendation: 'APPROVE' | 'MANUAL_REVIEW' | 'REJECT';
  /** When the validation was performed */
  created_at: string;
}

/**
 * File upload progress information.
 */
export interface UploadProgress {
  /** Upload progress percentage (0-100) */
  progress: number;
  /** Whether upload is complete */
  complete: boolean;
  /** Upload error if any */
  error?: string;
}

/**
 * Document upload state for UI components.
 */
export interface DocumentUploadState {
  /** File being uploaded */
  file: File | null;
  /** Upload progress */
  progress: UploadProgress;
  /** Processing response after upload */
  response?: DocumentProcessingResponse;
  /** Whether document is being processed */
  isProcessing: boolean;
  /** Processing error message */
  error?: string;
}
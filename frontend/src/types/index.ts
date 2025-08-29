/**
 * Re-export all type definitions for easier imports.
 */

export type {
  PersonalInfoFormData,
  PersonalInfoRequest,
  ApplicationResponse,
  ApplicationStatus,
  ApplicationUpdateRequest,
  FormErrors,
  ApiErrorResponse,
} from './application';

export type {
  DocumentType,
  ProcessingStatus,
  DocumentUploadRequest,
  GovernmentIdData,
  EmployerDocumentData,
  DocumentProcessingResponse,
  DocumentStatusResponse,
  ValidationResult,
  DocumentValidationResponse,
  UploadProgress,
  DocumentUploadState,
} from './document';
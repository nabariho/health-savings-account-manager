/**
 * Type definitions for HSA application data.
 * 
 * These types match the backend API schemas and provide type safety
 * throughout the frontend application.
 */

/**
 * Personal information form data.
 * Used for collecting user input before API submission.
 */
export interface PersonalInfoFormData {
  /** Applicant's full legal name */
  fullName: string;
  /** Applicant's date of birth in YYYY-MM-DD format */
  dateOfBirth: string;
  /** Street address */
  addressStreet: string;
  /** City name */
  addressCity: string;
  /** State abbreviation (2 letters) */
  addressState: string;
  /** ZIP or postal code */
  addressZip: string;
  /** Social Security Number */
  socialSecurityNumber: string;
  /** Current employer name */
  employerName: string;
}

/**
 * Personal information request payload for API.
 * Matches backend PersonalInfoRequest schema.
 */
export interface PersonalInfoRequest {
  /** Applicant's full legal name */
  full_name: string;
  /** Applicant's date of birth in YYYY-MM-DD format */
  date_of_birth: string;
  /** Street address */
  address_street: string;
  /** City name */
  address_city: string;
  /** State abbreviation (2 letters) */
  address_state: string;
  /** ZIP or postal code */
  address_zip: string;
  /** Social Security Number */
  social_security_number: string;
  /** Current employer name */
  employer_name: string;
}

/**
 * Application response from API.
 * Matches backend ApplicationResponse schema.
 */
export interface ApplicationResponse {
  /** Application unique identifier */
  id: string;
  /** Applicant's full legal name */
  full_name: string;
  /** Applicant's date of birth in YYYY-MM-DD format */
  date_of_birth: string;
  /** Street address */
  address_street: string;
  /** City name */
  address_city: string;
  /** State abbreviation (2 letters) */
  address_state: string;
  /** ZIP or postal code */
  address_zip: string;
  /** Social Security Number (masked for security) */
  social_security_number: string;
  /** Current employer name */
  employer_name: string;
  /** Application status */
  status: ApplicationStatus;
  /** When the application was created */
  created_at: string;
  /** When the application was last updated */
  updated_at: string;
}

/**
 * Application status enumeration.
 */
export type ApplicationStatus = 
  | 'pending'
  | 'processing' 
  | 'approved'
  | 'rejected'
  | 'manual_review';

/**
 * Application update request payload.
 * Used for updating existing applications.
 */
export interface ApplicationUpdateRequest {
  /** Applicant's full legal name */
  full_name?: string;
  /** Applicant's date of birth in YYYY-MM-DD format */
  date_of_birth?: string;
  /** Street address */
  address_street?: string;
  /** City name */
  address_city?: string;
  /** State abbreviation (2 letters) */
  address_state?: string;
  /** ZIP or postal code */
  address_zip?: string;
  /** Current employer name */
  employer_name?: string;
}

/**
 * Form validation errors.
 */
export interface FormErrors {
  [key: string]: string | undefined;
}

/**
 * API error response.
 */
export interface ApiErrorResponse {
  /** Indicates this is an error response */
  error: boolean;
  /** Error message */
  message: string;
  /** HTTP status code */
  status_code: number;
}
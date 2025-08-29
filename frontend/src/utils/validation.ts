/**
 * Validation schemas using Zod for form validation.
 * 
 * These schemas provide client-side validation that mirrors the backend
 * Pydantic validation rules, ensuring consistent data validation across
 * the application.
 */

import { z } from 'zod';

/**
 * US states for validation.
 */
const US_STATES = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
  'DC'
] as const;

/**
 * Personal information form validation schema.
 * 
 * Validates all required fields for HSA application creation.
 */
export const personalInfoSchema = z.object({
  fullName: z
    .string()
    .min(2, 'Full name must be at least 2 characters')
    .max(100, 'Full name must not exceed 100 characters')
    .regex(
      /^[a-zA-Z\s\-\.\,']+$/,
      'Full name can only contain letters, spaces, hyphens, periods, commas, and apostrophes'
    )
    .refine((val) => val.trim().length > 0, {
      message: 'Full name is required',
    }),

  dateOfBirth: z
    .string()
    .min(1, 'Date of birth is required')
    .refine((val) => {
      const date = new Date(val);
      return !isNaN(date.getTime());
    }, {
      message: 'Please enter a valid date',
    })
    .refine((val) => {
      const date = new Date(val);
      const today = new Date();
      return date < today;
    }, {
      message: 'Date of birth cannot be in the future',
    })
    .refine((val) => {
      const date = new Date(val);
      const today = new Date();
      const age = today.getFullYear() - date.getFullYear() - 
        (today.getMonth() < date.getMonth() || 
         (today.getMonth() === date.getMonth() && today.getDate() < date.getDate()) ? 1 : 0);
      return age >= 18;
    }, {
      message: 'Applicant must be at least 18 years old',
    })
    .refine((val) => {
      const date = new Date(val);
      const today = new Date();
      const age = today.getFullYear() - date.getFullYear();
      return age <= 120;
    }, {
      message: 'Please enter a valid date of birth',
    }),

  addressStreet: z
    .string()
    .min(5, 'Street address must be at least 5 characters')
    .max(200, 'Street address must not exceed 200 characters')
    .refine((val) => val.trim().length > 0, {
      message: 'Street address is required',
    }),

  addressCity: z
    .string()
    .min(2, 'City must be at least 2 characters')
    .max(50, 'City must not exceed 50 characters')
    .regex(
      /^[a-zA-Z\s\-\.\']+$/,
      'City can only contain letters, spaces, hyphens, periods, and apostrophes'
    )
    .refine((val) => val.trim().length > 0, {
      message: 'City is required',
    }),

  addressState: z
    .string()
    .length(2, 'State must be a 2-letter abbreviation')
    .refine((val) => US_STATES.includes(val.toUpperCase() as any), {
      message: 'Please select a valid US state',
    })
    .transform((val) => val.toUpperCase()),

  addressZip: z
    .string()
    .regex(
      /^\d{5}(-\d{4})?$/,
      'ZIP code must be in format XXXXX or XXXXX-XXXX'
    ),

  socialSecurityNumber: z
    .string()
    .min(1, 'Social Security Number is required')
    .refine((val) => {
      // Remove any non-digit characters for validation
      const digits = val.replace(/\D/g, '');
      return digits.length === 9;
    }, {
      message: 'Social Security Number must contain exactly 9 digits',
    })
    .refine((val) => {
      const digits = val.replace(/\D/g, '');
      // Check for invalid patterns
      return !(
        digits === '000000000' ||
        digits.startsWith('000') ||
        digits.substring(3, 5) === '00' ||
        digits.substring(5) === '0000'
      );
    }, {
      message: 'Please enter a valid Social Security Number',
    }),

  employerName: z
    .string()
    .min(2, 'Employer name must be at least 2 characters')
    .max(100, 'Employer name must not exceed 100 characters')
    .regex(
      /^[a-zA-Z0-9\s\-\.\,\'&]+$/,
      'Employer name contains invalid characters'
    )
    .refine((val) => val.trim().length > 0, {
      message: 'Employer name is required',
    }),
});

/**
 * Type inference from the schema.
 */
export type PersonalInfoFormData = z.infer<typeof personalInfoSchema>;

/**
 * Transform form data to API request format.
 * 
 * Converts camelCase form fields to snake_case API fields.
 * 
 * @param formData - Form data from React Hook Form
 * @returns API request payload
 */
export const transformFormDataToApiRequest = (formData: PersonalInfoFormData) => ({
  full_name: formData.fullName.trim(),
  date_of_birth: formData.dateOfBirth,
  address_street: formData.addressStreet.trim(),
  address_city: formData.addressCity.trim(),
  address_state: formData.addressState,
  address_zip: formData.addressZip,
  social_security_number: formData.socialSecurityNumber,
  employer_name: formData.employerName.trim(),
});

/**
 * Format SSN with dashes for display.
 * 
 * @param ssn - Raw SSN string
 * @returns Formatted SSN (XXX-XX-XXXX)
 */
export const formatSSN = (ssn: string): string => {
  const digits = ssn.replace(/\D/g, '');
  if (digits.length === 9) {
    return `${digits.slice(0, 3)}-${digits.slice(3, 5)}-${digits.slice(5)}`;
  }
  return ssn;
};

/**
 * Validation error messages for better UX.
 */
export const getFieldError = (errors: any, fieldName: string): string | undefined => {
  const error = errors[fieldName];
  return error?.message;
};
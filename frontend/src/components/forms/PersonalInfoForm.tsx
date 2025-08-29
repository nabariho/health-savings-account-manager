/**
 * Personal Information Form component.
 * 
 * Handles the first step of HSA onboarding by collecting and validating
 * personal information required for identity verification and eligibility
 * determination.
 */

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';

import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Card, CardBody } from '@/components/ui/Card';
import { personalInfoSchema, transformFormDataToApiRequest, formatSSN } from '@/utils/validation';
import { applicationService } from '@/services/applicationService';
import type { PersonalInfoFormData, ApplicationResponse } from '@/types';

export interface PersonalInfoFormProps {
  /** Callback when application is successfully created */
  onSuccess?: (application: ApplicationResponse) => void;
  /** Initial form data for editing */
  initialData?: Partial<PersonalInfoFormData>;
}

/**
 * Personal Information Form component with validation and API integration.
 * 
 * Features:
 * - Client-side validation with Zod
 * - Real-time form validation feedback
 * - SSN formatting
 * - Loading states
 * - Error handling
 * 
 * @param props - Component props
 * @returns JSX.Element
 */
export const PersonalInfoForm: React.FC<PersonalInfoFormProps> = ({
  onSuccess,
  initialData,
}) => {
  const [apiError, setApiError] = useState<string | null>(null);

  // Setup form with validation
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    setValue,
    watch,
  } = useForm<PersonalInfoFormData>({
    resolver: zodResolver(personalInfoSchema),
    mode: 'onBlur',
    defaultValues: initialData || {
      fullName: '',
      dateOfBirth: '',
      addressStreet: '',
      addressCity: '',
      addressState: '',
      addressZip: '',
      socialSecurityNumber: '',
      employerName: '',
    },
  });

  // API mutation for creating application
  const createApplicationMutation = useMutation({
    mutationFn: applicationService.createApplication,
    onSuccess: (data) => {
      setApiError(null);
      onSuccess?.(data);
    },
    onError: (error: any) => {
      setApiError(error.message || 'Failed to create application');
    },
  });

  // Handle form submission
  const onSubmit = async (data: PersonalInfoFormData) => {
    setApiError(null);
    const apiRequest = transformFormDataToApiRequest(data);
    createApplicationMutation.mutate(apiRequest);
  };

  // Watch SSN field for formatting
  const ssnValue = watch('socialSecurityNumber');

  // Format SSN as user types
  const handleSSNChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const formatted = formatSSN(value);
    setValue('socialSecurityNumber', formatted, { shouldValidate: true });
  };

  const isLoading = createApplicationMutation.isPending;

  return (
    <Card>
      <CardBody>
        <div className="space-y-6">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900">
              Personal Information
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              Please provide your personal information to begin your HSA application.
              All fields are required.
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* API Error Display */}
            {apiError && (
              <div className="rounded-md bg-red-50 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-5 w-5 text-red-400"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">
                      Error creating application
                    </h3>
                    <div className="mt-2 text-sm text-red-700">
                      {apiError}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Personal Information Fields */}
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div className="md:col-span-2">
                <Input
                  {...register('fullName')}
                  label="Full Legal Name"
                  placeholder="John Doe"
                  error={errors.fullName?.message}
                  required
                  disabled={isLoading}
                />
              </div>

              <Input
                {...register('dateOfBirth')}
                type="date"
                label="Date of Birth"
                error={errors.dateOfBirth?.message}
                required
                disabled={isLoading}
              />

              <Input
                {...register('socialSecurityNumber')}
                label="Social Security Number"
                placeholder="123-45-6789"
                error={errors.socialSecurityNumber?.message}
                onChange={handleSSNChange}
                maxLength={11}
                required
                disabled={isLoading}
              />
            </div>

            {/* Address Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 border-b border-gray-200 pb-2">
                Address Information
              </h3>

              <Input
                {...register('addressStreet')}
                label="Street Address"
                placeholder="123 Main Street"
                error={errors.addressStreet?.message}
                required
                disabled={isLoading}
              />

              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <Input
                  {...register('addressCity')}
                  label="City"
                  placeholder="Anytown"
                  error={errors.addressCity?.message}
                  required
                  disabled={isLoading}
                />

                <Input
                  {...register('addressState')}
                  label="State"
                  placeholder="CA"
                  maxLength={2}
                  error={errors.addressState?.message}
                  required
                  disabled={isLoading}
                />

                <Input
                  {...register('addressZip')}
                  label="ZIP Code"
                  placeholder="12345"
                  error={errors.addressZip?.message}
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Employment Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 border-b border-gray-200 pb-2">
                Employment Information
              </h3>

              <Input
                {...register('employerName')}
                label="Current Employer"
                placeholder="Acme Corporation"
                error={errors.employerName?.message}
                required
                disabled={isLoading}
              />
            </div>

            {/* Submit Button */}
            <div className="pt-6">
              <Button
                type="submit"
                fullWidth
                loading={isLoading}
                disabled={!isValid || isLoading}
              >
                {isLoading ? 'Creating Application...' : 'Create HSA Application'}
              </Button>
            </div>

            {/* Form Help Text */}
            <div className="mt-4 text-center">
              <p className="text-xs text-gray-500">
                By submitting this form, you acknowledge that the information provided
                is accurate and complete. This information will be used for identity
                verification and HSA eligibility determination.
              </p>
            </div>
          </form>
        </div>
      </CardBody>
    </Card>
  );
};
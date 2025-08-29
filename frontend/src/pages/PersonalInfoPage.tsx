/**
 * Personal Information Page component.
 * 
 * First step of HSA onboarding process where users provide
 * personal information required for identity verification.
 */

import React, { useState } from 'react';
import { PersonalInfoForm } from '@/components/forms/PersonalInfoForm';
import { Layout } from '@/components/layout/Layout';
import type { ApplicationResponse } from '@/types';

/**
 * Personal Information Page with form and success handling.
 * 
 * @returns JSX.Element
 */
export const PersonalInfoPage: React.FC = () => {
  const [applicationResult, setApplicationResult] = useState<ApplicationResponse | null>(null);

  const handleApplicationSuccess = (application: ApplicationResponse) => {
    setApplicationResult(application);
  };

  const handleStartOver = () => {
    setApplicationResult(null);
  };

  return (
    <Layout>
      <div className="space-y-8">
        {/* Page Header */}
        <div className="text-center">
          <div className="inline-flex items-center space-x-2 text-primary-600 mb-4">
            <div className="w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
              1
            </div>
            <span className="text-lg font-medium">Step 1 of 4</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">
            Start Your HSA Application
          </h1>
          <p className="mt-4 text-lg text-gray-600 max-w-2xl mx-auto">
            Welcome to the Health Savings Account onboarding process. 
            We'll start by collecting some basic information about you.
          </p>
        </div>

        {/* Progress Bar */}
        <div className="max-w-md mx-auto">
          <div className="flex items-center justify-between text-sm text-gray-500 mb-2">
            <span>Personal Info</span>
            <span>Documents</span>
            <span>Questions</span>
            <span>Decision</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-primary-600 h-2 rounded-full" style={{ width: '25%' }}></div>
          </div>
        </div>

        {/* Success Message */}
        {applicationResult && (
          <div className="max-w-2xl mx-auto">
            <div className="rounded-md bg-green-50 p-6 border border-green-200">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-green-400"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-green-800">
                    Application Created Successfully
                  </h3>
                  <div className="mt-2 text-sm text-green-700">
                    <p className="mb-3">
                      Your HSA application has been created with ID:{' '}
                      <span className="font-mono font-medium">
                        {applicationResult.id}
                      </span>
                    </p>
                    <div className="bg-white rounded-md p-4 border border-green-200">
                      <h4 className="font-medium text-green-800 mb-2">Application Summary:</h4>
                      <dl className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                        <div>
                          <dt className="text-xs font-medium text-green-700">Name:</dt>
                          <dd className="text-xs text-green-900">{applicationResult.full_name}</dd>
                        </div>
                        <div>
                          <dt className="text-xs font-medium text-green-700">Date of Birth:</dt>
                          <dd className="text-xs text-green-900">{applicationResult.date_of_birth}</dd>
                        </div>
                        <div>
                          <dt className="text-xs font-medium text-green-700">Status:</dt>
                          <dd className="text-xs text-green-900 capitalize">{applicationResult.status}</dd>
                        </div>
                        <div>
                          <dt className="text-xs font-medium text-green-700">Employer:</dt>
                          <dd className="text-xs text-green-900">{applicationResult.employer_name}</dd>
                        </div>
                      </dl>
                    </div>
                  </div>
                  <div className="mt-4">
                    <button
                      type="button"
                      onClick={handleStartOver}
                      className="text-sm font-medium text-green-800 hover:text-green-900"
                    >
                      Create Another Application →
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Form */}
        {!applicationResult && (
          <div className="max-w-2xl mx-auto">
            <PersonalInfoForm onSuccess={handleApplicationSuccess} />
          </div>
        )}

        {/* Information Panel */}
        <div className="max-w-4xl mx-auto mt-12">
          <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
            <h3 className="text-lg font-medium text-blue-900 mb-4">
              Why We Need This Information
            </h3>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div>
                <h4 className="font-medium text-blue-800 mb-2">Identity Verification</h4>
                <p className="text-sm text-blue-700">
                  We use your personal information to verify your identity and ensure
                  compliance with financial regulations (KYC/CIP requirements).
                </p>
              </div>
              <div>
                <h4 className="font-medium text-blue-800 mb-2">Eligibility Determination</h4>
                <p className="text-sm text-blue-700">
                  Your employment and personal details help us determine your
                  eligibility for a Health Savings Account.
                </p>
              </div>
              <div>
                <h4 className="font-medium text-blue-800 mb-2">Security & Privacy</h4>
                <p className="text-sm text-blue-700">
                  All information is encrypted and stored securely. Your data is
                  never shared with third parties without your consent.
                </p>
              </div>
              <div>
                <h4 className="font-medium text-blue-800 mb-2">Next Steps</h4>
                <p className="text-sm text-blue-700">
                  After submitting this information, you'll upload documents
                  for verification and have a chance to ask questions about HSAs.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};
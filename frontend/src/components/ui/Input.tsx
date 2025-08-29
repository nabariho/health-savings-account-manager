/**
 * Input component with consistent styling and validation support.
 * 
 * Provides a reusable input field with proper accessibility,
 * error handling, and Tailwind CSS styling.
 */

import React from 'react';
import clsx from 'clsx';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Input label */
  label?: string;
  /** Error message */
  error?: string;
  /** Help text */
  helpText?: string;
  /** Required field indicator */
  required?: boolean;
}

/**
 * Input component with label, validation, and help text support.
 * 
 * @param props - Input properties
 * @returns JSX.Element
 */
export const Input: React.FC<InputProps> = ({
  id,
  label,
  error,
  helpText,
  required,
  className,
  ...props
}) => {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, '_');

  const inputClasses = clsx([
    'block',
    'w-full',
    'rounded-md',
    'border-gray-300',
    'shadow-sm',
    'focus:border-primary-500',
    'focus:ring-primary-500',
    'sm:text-sm',
    error && [
      'border-red-300',
      'text-red-900',
      'placeholder-red-300',
      'focus:border-red-500',
      'focus:ring-red-500',
    ],
    className,
  ]);

  return (
    <div className="space-y-1">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-gray-700"
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      <div className="relative">
        <input
          id={inputId}
          className={inputClasses}
          aria-describedby={
            error ? `${inputId}-error` : helpText ? `${inputId}-help` : undefined
          }
          aria-invalid={error ? 'true' : 'false'}
          {...props}
        />
        
        {error && (
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
            <svg
              className="h-5 w-5 text-red-500"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        )}
      </div>

      {error && (
        <p id={`${inputId}-error`} className="text-sm text-red-600">
          {error}
        </p>
      )}

      {helpText && !error && (
        <p id={`${inputId}-help`} className="text-sm text-gray-500">
          {helpText}
        </p>
      )}
    </div>
  );
};
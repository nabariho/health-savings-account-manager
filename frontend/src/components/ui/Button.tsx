/**
 * Button component with Tailwind CSS styling.
 * 
 * Provides consistent button styling throughout the application
 * with support for different variants and states.
 */

import React from 'react';
import clsx from 'clsx';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Button variant for different styling */
  variant?: 'primary' | 'secondary' | 'outline' | 'danger';
  /** Button size */
  size?: 'sm' | 'md' | 'lg';
  /** Loading state */
  loading?: boolean;
  /** Full width button */
  fullWidth?: boolean;
}

/**
 * Button component with consistent styling and behavior.
 * 
 * @param props - Button properties
 * @returns JSX.Element
 */
export const Button: React.FC<ButtonProps> = ({
  children,
  className,
  variant = 'primary',
  size = 'md',
  loading = false,
  fullWidth = false,
  disabled,
  ...props
}) => {
  const baseClasses = [
    'inline-flex',
    'items-center',
    'justify-center',
    'font-medium',
    'rounded-md',
    'border',
    'transition-colors',
    'focus:outline-none',
    'focus:ring-2',
    'focus:ring-offset-2',
    'disabled:opacity-50',
    'disabled:cursor-not-allowed',
  ];

  const variantClasses = {
    primary: [
      'bg-primary-600',
      'border-transparent',
      'text-white',
      'hover:bg-primary-700',
      'focus:ring-primary-500',
      'disabled:hover:bg-primary-600',
    ],
    secondary: [
      'bg-gray-100',
      'border-transparent',
      'text-gray-900',
      'hover:bg-gray-200',
      'focus:ring-gray-500',
      'disabled:hover:bg-gray-100',
    ],
    outline: [
      'bg-white',
      'border-gray-300',
      'text-gray-700',
      'hover:bg-gray-50',
      'focus:ring-primary-500',
      'disabled:hover:bg-white',
    ],
    danger: [
      'bg-red-600',
      'border-transparent',
      'text-white',
      'hover:bg-red-700',
      'focus:ring-red-500',
      'disabled:hover:bg-red-600',
    ],
  };

  const sizeClasses = {
    sm: ['px-3', 'py-2', 'text-sm'],
    md: ['px-4', 'py-2', 'text-sm'],
    lg: ['px-6', 'py-3', 'text-base'],
  };

  const widthClasses = fullWidth ? ['w-full'] : [];

  const buttonClasses = clsx([
    ...baseClasses,
    ...variantClasses[variant],
    ...sizeClasses[size],
    ...widthClasses,
    className,
  ]);

  return (
    <button
      className={buttonClasses}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg
          className="-ml-1 mr-2 h-4 w-4 animate-spin"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          ></circle>
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
      )}
      {children}
    </button>
  );
};
/**
 * Card component for consistent content containers.
 * 
 * Provides a reusable card layout with optional header, body, and footer
 * sections with consistent Tailwind CSS styling.
 */

import React from 'react';
import clsx from 'clsx';

export interface CardProps {
  /** Card content */
  children: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
  /** Card padding variant */
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export interface CardHeaderProps {
  /** Header content */
  children: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
}

export interface CardBodyProps {
  /** Body content */
  children: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
}

export interface CardFooterProps {
  /** Footer content */
  children: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Main Card component.
 * 
 * @param props - Card properties
 * @returns JSX.Element
 */
export const Card: React.FC<CardProps> = ({
  children,
  className,
  padding = 'md',
}) => {
  const baseClasses = [
    'bg-white',
    'shadow-sm',
    'rounded-lg',
    'border',
    'border-gray-200',
  ];

  const paddingClasses = {
    none: [],
    sm: ['p-4'],
    md: ['p-6'],
    lg: ['p-8'],
  };

  const cardClasses = clsx([
    ...baseClasses,
    ...paddingClasses[padding],
    className,
  ]);

  return <div className={cardClasses}>{children}</div>;
};

/**
 * Card header component.
 * 
 * @param props - Card header properties
 * @returns JSX.Element
 */
export const CardHeader: React.FC<CardHeaderProps> = ({
  children,
  className,
}) => {
  const headerClasses = clsx([
    'px-6',
    'py-4',
    'border-b',
    'border-gray-200',
    'bg-gray-50',
    'rounded-t-lg',
    className,
  ]);

  return <div className={headerClasses}>{children}</div>;
};

/**
 * Card body component.
 * 
 * @param props - Card body properties
 * @returns JSX.Element
 */
export const CardBody: React.FC<CardBodyProps> = ({
  children,
  className,
}) => {
  const bodyClasses = clsx(['p-6', className]);

  return <div className={bodyClasses}>{children}</div>;
};

/**
 * Card footer component.
 * 
 * @param props - Card footer properties
 * @returns JSX.Element
 */
export const CardFooter: React.FC<CardFooterProps> = ({
  children,
  className,
}) => {
  const footerClasses = clsx([
    'px-6',
    'py-4',
    'border-t',
    'border-gray-200',
    'bg-gray-50',
    'rounded-b-lg',
    className,
  ]);

  return <div className={footerClasses}>{children}</div>;
};
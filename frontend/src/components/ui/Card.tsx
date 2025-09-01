/**
 * Card component for consistent container styling.
 */

import React from 'react';
import clsx from 'clsx';

export interface CardProps {
  /** Card content */
  children: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Card component with consistent styling.
 */
export const Card: React.FC<CardProps> = ({ children, className }) => {
  return (
    <div
      className={clsx(
        'bg-white border border-gray-200 rounded-lg shadow-sm',
        className
      )}
    >
      {children}
    </div>
  );
};

export interface CardBodyProps {
  /** Card body content */
  children: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Card body component for content within cards.
 */
export const CardBody: React.FC<CardBodyProps> = ({ children, className }) => {
  return (
    <div
      className={clsx('p-6', className)}
    >
      {children}
    </div>
  );
};

export default Card;

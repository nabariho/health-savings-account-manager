/**
 * Toast notification system for user feedback.
 * 
 * Provides temporary notifications for actions like copy, feedback submission,
 * and other user interactions with appropriate styling and animations.
 */

import React, { useState, useEffect, createContext, useContext, useCallback } from 'react';
import clsx from 'clsx';

/**
 * Toast type definitions.
 */
export type ToastType = 'success' | 'error' | 'info' | 'warning';

/**
 * Toast message interface.
 */
export interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

/**
 * Toast context interface.
 */
interface ToastContextValue {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  clearToasts: () => void;
}

/**
 * Toast context.
 */
const ToastContext = createContext<ToastContextValue | undefined>(undefined);

/**
 * Generate unique toast ID.
 */
function generateToastId(): string {
  return `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Toast provider props.
 */
interface ToastProviderProps {
  children: React.ReactNode;
  maxToasts?: number;
}

/**
 * Toast provider component.
 */
export const ToastProvider: React.FC<ToastProviderProps> = ({ 
  children, 
  maxToasts = 5 
}) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  /**
   * Add a new toast.
   */
  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const newToast: Toast = {
      ...toast,
      id: generateToastId(),
      duration: toast.duration ?? 4000,
    };

    setToasts(prev => {
      const updated = [...prev, newToast];
      // Keep only the most recent toasts
      return updated.slice(-maxToasts);
    });

    // Auto-remove toast after duration
    if (newToast.duration && newToast.duration > 0) {
      setTimeout(() => {
        removeToast(newToast.id);
      }, newToast.duration);
    }
  }, [maxToasts]);

  /**
   * Remove a toast by ID.
   */
  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  /**
   * Clear all toasts.
   */
  const clearToasts = useCallback(() => {
    setToasts([]);
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, clearToasts }}>
      {children}
      <ToastContainer />
    </ToastContext.Provider>
  );
};

/**
 * Toast container component.
 */
const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {toasts.map(toast => (
        <ToastItem
          key={toast.id}
          toast={toast}
          onClose={() => removeToast(toast.id)}
        />
      ))}
    </div>
  );
};

/**
 * Individual toast item props.
 */
interface ToastItemProps {
  toast: Toast;
  onClose: () => void;
}

/**
 * Individual toast item component.
 */
const ToastItem: React.FC<ToastItemProps> = ({ toast, onClose }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);

  // Animate in
  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), 50);
    return () => clearTimeout(timer);
  }, []);

  /**
   * Handle close with animation.
   */
  const handleClose = () => {
    setIsLeaving(true);
    setTimeout(onClose, 200);
  };

  /**
   * Get toast styling based on type.
   */
  const getToastClasses = () => {
    const baseClasses = 'rounded-lg shadow-lg border p-4 min-w-80 max-w-md transform transition-all duration-200 ease-in-out';
    
    const visibilityClasses = isVisible && !isLeaving
      ? 'translate-x-0 opacity-100'
      : 'translate-x-full opacity-0';

    const typeClasses = {
      success: 'bg-green-50 border-green-200 text-green-800',
      error: 'bg-red-50 border-red-200 text-red-800',
      warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      info: 'bg-blue-50 border-blue-200 text-blue-800',
    };

    return clsx(baseClasses, visibilityClasses, typeClasses[toast.type]);
  };

  /**
   * Get icon for toast type.
   */
  const getIcon = () => {
    const iconClasses = 'w-5 h-5 flex-shrink-0';
    
    switch (toast.type) {
      case 'success':
        return (
          <svg className={clsx(iconClasses, 'text-green-400')} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'error':
        return (
          <svg className={clsx(iconClasses, 'text-red-400')} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      case 'warning':
        return (
          <svg className={clsx(iconClasses, 'text-yellow-400')} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'info':
        return (
          <svg className={clsx(iconClasses, 'text-blue-400')} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  return (
    <div className={getToastClasses()}>
      <div className="flex items-start">
        {/* Icon */}
        <div className="flex-shrink-0">
          {getIcon()}
        </div>

        {/* Content */}
        <div className="ml-3 flex-1">
          <p className="text-sm font-medium">
            {toast.message}
          </p>
        </div>

        {/* Action button */}
        {toast.action && (
          <div className="ml-4">
            <button
              onClick={toast.action.onClick}
              className="text-sm font-medium underline hover:no-underline focus:outline-none"
            >
              {toast.action.label}
            </button>
          </div>
        )}

        {/* Close button */}
        <div className="ml-4 flex-shrink-0">
          <button
            onClick={handleClose}
            className="rounded-md inline-flex text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <span className="sr-only">Close</span>
            <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

/**
 * Hook to use toast notifications.
 */
export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  
  return context;
}

/**
 * Convenience hook for common toast actions.
 */
export function useToastActions() {
  const { addToast } = useToast();

  return {
    success: (message: string, options?: Partial<Omit<Toast, 'id' | 'type' | 'message'>>) =>
      addToast({ message, type: 'success', ...options }),
    
    error: (message: string, options?: Partial<Omit<Toast, 'id' | 'type' | 'message'>>) =>
      addToast({ message, type: 'error', ...options }),
    
    info: (message: string, options?: Partial<Omit<Toast, 'id' | 'type' | 'message'>>) =>
      addToast({ message, type: 'info', ...options }),
    
    warning: (message: string, options?: Partial<Omit<Toast, 'id' | 'type' | 'message'>>) =>
      addToast({ message, type: 'warning', ...options }),
  };
}

export default ToastProvider;
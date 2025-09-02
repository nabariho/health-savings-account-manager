/**
 * Comprehensive tests for Toast notification system.
 * 
 * Tests toast functionality including:
 * - Toast provider context management
 * - Different toast types (success, error, info, warning)
 * - Toast lifecycle (show, auto-dismiss, manual dismiss)
 * - Toast positioning and animations
 * - Multiple toast management and limits
 * - Action buttons and interactions
 * - Accessibility compliance
 * - Hook-based toast utilities
 */

import React, { useEffect } from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { vi } from 'vitest';
import { ToastProvider, useToast, useToastActions } from '../Toast';
import type { Toast } from '../Toast';

// Mock timers for auto-dismiss testing
vi.useFakeTimers();

// Test component that uses toast hooks
const TestToastConsumer: React.FC<{
  onMount?: (toastActions: ReturnType<typeof useToast>) => void;
}> = ({ onMount }) => {
  const toastContext = useToast();
  
  useEffect(() => {
    if (onMount) {
      onMount(toastContext);
    }
  }, [onMount, toastContext]);

  return (
    <div>
      <span data-testid="toast-count">{toastContext.toasts.length}</span>
      <button
        onClick={() => toastContext.addToast({
          message: 'Test toast',
          type: 'success',
        })}
      >
        Add Toast
      </button>
      <button
        onClick={() => toastContext.clearToasts()}
      >
        Clear All
      </button>
    </div>
  );
};

// Test component using toast action hooks
const TestToastActions: React.FC = () => {
  const { success, error, info, warning } = useToastActions();

  return (
    <div>
      <button onClick={() => success('Success message')}>Success Toast</button>
      <button onClick={() => error('Error message')}>Error Toast</button>
      <button onClick={() => info('Info message')}>Info Toast</button>
      <button onClick={() => warning('Warning message')}>Warning Toast</button>
    </div>
  );
};

describe('Toast System', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.clearAllTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  describe('ToastProvider', () => {
    it('provides toast context to children', () => {
      const mockOnMount = vi.fn();

      render(
        <ToastProvider>
          <TestToastConsumer onMount={mockOnMount} />
        </ToastProvider>
      );

      expect(mockOnMount).toHaveBeenCalledWith(
        expect.objectContaining({
          toasts: [],
          addToast: expect.any(Function),
          removeToast: expect.any(Function),
          clearToasts: expect.any(Function),
        })
      );
    });

    it('throws error when useToast is used outside provider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        render(<TestToastConsumer />);
      }).toThrow('useToast must be used within a ToastProvider');

      consoleSpy.mockRestore();
    });

    it('respects maxToasts limit', async () => {
      let toastActions: ReturnType<typeof useToast>;

      render(
        <ToastProvider maxToasts={3}>
          <TestToastConsumer
            onMount={(actions) => {
              toastActions = actions;
            }}
          />
        </ToastProvider>
      );

      // Add 5 toasts, should only keep the last 3
      act(() => {
        toastActions.addToast({ message: 'Toast 1', type: 'info' });
        toastActions.addToast({ message: 'Toast 2', type: 'info' });
        toastActions.addToast({ message: 'Toast 3', type: 'info' });
        toastActions.addToast({ message: 'Toast 4', type: 'info' });
        toastActions.addToast({ message: 'Toast 5', type: 'info' });
      });

      expect(screen.getByTestId('toast-count')).toHaveTextContent('3');
      
      // Should show the last 3 toasts
      expect(screen.getByText('Toast 3')).toBeInTheDocument();
      expect(screen.getByText('Toast 4')).toBeInTheDocument();
      expect(screen.getByText('Toast 5')).toBeInTheDocument();
      expect(screen.queryByText('Toast 1')).not.toBeInTheDocument();
      expect(screen.queryByText('Toast 2')).not.toBeInTheDocument();
    });
  });

  describe('Toast Display and Types', () => {
    it('displays success toast with correct styling and icon', async () => {
      render(
        <ToastProvider>
          <TestToastActions />
        </ToastProvider>
      );

      fireEvent.click(screen.getByText('Success Toast'));

      await waitFor(() => {
        expect(screen.getByText('Success message')).toBeInTheDocument();
      });

      const toast = screen.getByText('Success message').closest('div');
      expect(toast).toHaveClass('bg-green-50', 'border-green-200', 'text-green-800');

      // Should have success icon (checkmark)
      const icon = toast?.querySelector('svg');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('text-green-400');
    });

    it('displays error toast with correct styling and icon', async () => {
      render(
        <ToastProvider>
          <TestToastActions />
        </ToastProvider>
      );

      fireEvent.click(screen.getByText('Error Toast'));

      await waitFor(() => {
        expect(screen.getByText('Error message')).toBeInTheDocument();
      });

      const toast = screen.getByText('Error message').closest('div');
      expect(toast).toHaveClass('bg-red-50', 'border-red-200', 'text-red-800');

      // Should have error icon (X)
      const icon = toast?.querySelector('svg');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('text-red-400');
    });

    it('displays info toast with correct styling and icon', async () => {
      render(
        <ToastProvider>
          <TestToastActions />
        </ToastProvider>
      );

      fireEvent.click(screen.getByText('Info Toast'));

      await waitFor(() => {
        expect(screen.getByText('Info message')).toBeInTheDocument();
      });

      const toast = screen.getByText('Info message').closest('div');
      expect(toast).toHaveClass('bg-blue-50', 'border-blue-200', 'text-blue-800');

      // Should have info icon
      const icon = toast?.querySelector('svg');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('text-blue-400');
    });

    it('displays warning toast with correct styling and icon', async () => {
      render(
        <ToastProvider>
          <TestToastActions />
        </ToastProvider>
      );

      fireEvent.click(screen.getByText('Warning Toast'));

      await waitFor(() => {
        expect(screen.getByText('Warning message')).toBeInTheDocument();
      });

      const toast = screen.getByText('Warning message').closest('div');
      expect(toast).toHaveClass('bg-yellow-50', 'border-yellow-200', 'text-yellow-800');

      // Should have warning icon (triangle with exclamation)
      const icon = toast?.querySelector('svg');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('text-yellow-400');
    });
  });

  describe('Toast Lifecycle and Auto-dismiss', () => {
    it('auto-dismisses toast after default duration', async () => {
      let toastActions: ReturnType<typeof useToast>;

      render(
        <ToastProvider>
          <TestToastConsumer
            onMount={(actions) => {
              toastActions = actions;
            }}
          />
        </ToastProvider>
      );

      act(() => {
        toastActions.addToast({
          message: 'Auto-dismiss toast',
          type: 'success',
        });
      });

      // Toast should be visible
      await waitFor(() => {
        expect(screen.getByText('Auto-dismiss toast')).toBeInTheDocument();
      });

      // Fast-forward past default duration (4000ms)
      act(() => {
        vi.advanceTimersByTime(4000);
      });

      await waitFor(() => {
        expect(screen.queryByText('Auto-dismiss toast')).not.toBeInTheDocument();
      });
    });

    it('auto-dismisses toast after custom duration', async () => {
      let toastActions: ReturnType<typeof useToast>;

      render(
        <ToastProvider>
          <TestToastConsumer
            onMount={(actions) => {
              toastActions = actions;
            }}
          />
        </ToastProvider>
      );

      act(() => {
        toastActions.addToast({
          message: 'Custom duration toast',
          type: 'success',
          duration: 2000,
        });
      });

      await waitFor(() => {
        expect(screen.getByText('Custom duration toast')).toBeInTheDocument();
      });

      // Should not dismiss before custom duration
      act(() => {
        vi.advanceTimersByTime(1500);
      });
      expect(screen.getByText('Custom duration toast')).toBeInTheDocument();

      // Should dismiss after custom duration
      act(() => {
        vi.advanceTimersByTime(500);
      });

      await waitFor(() => {
        expect(screen.queryByText('Custom duration toast')).not.toBeInTheDocument();
      });
    });

    it('does not auto-dismiss when duration is 0', async () => {
      let toastActions: ReturnType<typeof useToast>;

      render(
        <ToastProvider>
          <TestToastConsumer
            onMount={(actions) => {
              toastActions = actions;
            }}
          />
        </ToastProvider>
      );

      act(() => {
        toastActions.addToast({
          message: 'Persistent toast',
          type: 'success',
          duration: 0,
        });
      });

      await waitFor(() => {
        expect(screen.getByText('Persistent toast')).toBeInTheDocument();
      });

      // Should not dismiss even after long duration
      act(() => {
        vi.advanceTimersByTime(10000);
      });

      expect(screen.getByText('Persistent toast')).toBeInTheDocument();
    });

    it('allows manual dismissal via close button', async () => {
      let toastActions: ReturnType<typeof useToast>;

      render(
        <ToastProvider>
          <TestToastConsumer
            onMount={(actions) => {
              toastActions = actions;
            }}
          />
        </ToastProvider>
      );

      act(() => {
        toastActions.addToast({
          message: 'Manual dismiss toast',
          type: 'info',
          duration: 0, // Prevent auto-dismiss
        });
      });

      await waitFor(() => {
        expect(screen.getByText('Manual dismiss toast')).toBeInTheDocument();
      });

      // Find and click close button
      const closeButton = screen.getByRole('button', { name: /close/i });
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByText('Manual dismiss toast')).not.toBeInTheDocument();
      });
    });
  });

  describe('Toast Animations', () => {
    it('animates toast entry', async () => {
      let toastActions: ReturnType<typeof useToast>;

      render(
        <ToastProvider>
          <TestToastConsumer
            onMount={(actions) => {
              toastActions = actions;
            }}
          />
        </ToastProvider>
      );

      act(() => {
        toastActions.addToast({
          message: 'Animated toast',
          type: 'success',
        });
      });

      await waitFor(() => {
        const toast = screen.getByText('Animated toast').closest('div');
        expect(toast).toHaveClass('transform', 'transition-all', 'duration-200');
      });
    });

    it('animates toast exit on close', async () => {
      let toastActions: ReturnType<typeof useToast>;

      render(
        <ToastProvider>
          <TestToastConsumer
            onMount={(actions) => {
              toastActions = actions;
            }}
          />
        </ToastProvider>
      );

      act(() => {
        toastActions.addToast({
          message: 'Exit animation toast',
          type: 'success',
          duration: 0,
        });
      });

      await waitFor(() => {
        expect(screen.getByText('Exit animation toast')).toBeInTheDocument();
      });

      // Click close button
      const closeButton = screen.getByRole('button', { name: /close/i });
      fireEvent.click(closeButton);

      // Should have exit animation classes
      const toast = screen.getByText('Exit animation toast').closest('div');
      expect(toast).toHaveClass('translate-x-full', 'opacity-0');
    });
  });

  describe('Toast Actions', () => {
    it('displays action button when provided', async () => {
      let toastActions: ReturnType<typeof useToast>;

      render(
        <ToastProvider>
          <TestToastConsumer
            onMount={(actions) => {
              toastActions = actions;
            }}
          />
        </ToastProvider>
      );

      const mockActionCallback = vi.fn();

      act(() => {
        toastActions.addToast({
          message: 'Toast with action',
          type: 'info',
          duration: 0,
          action: {
            label: 'Retry',
            onClick: mockActionCallback,
          },
        });
      });

      await waitFor(() => {
        expect(screen.getByText('Toast with action')).toBeInTheDocument();
        expect(screen.getByText('Retry')).toBeInTheDocument();
      });

      // Click action button
      fireEvent.click(screen.getByText('Retry'));
      expect(mockActionCallback).toHaveBeenCalledTimes(1);
    });

    it('styles action button correctly', async () => {
      let toastActions: ReturnType<typeof useToast>;

      render(
        <ToastProvider>
          <TestToastConsumer
            onMount={(actions) => {
              toastActions = actions;
            }}
          />
        </ToastProvider>
      );

      act(() => {
        toastActions.addToast({
          message: 'Toast with styled action',
          type: 'success',
          action: {
            label: 'Action',
            onClick: () => {},
          },
        });
      });

      await waitFor(() => {
        const actionButton = screen.getByText('Action');
        expect(actionButton).toHaveClass('text-sm', 'font-medium', 'underline', 'hover:no-underline');
      });
    });
  });

  describe('Multiple Toasts Management', () => {
    it('displays multiple toasts in correct order', async () => {
      let toastActions: ReturnType<typeof useToast>;

      render(
        <ToastProvider>
          <TestToastConsumer
            onMount={(actions) => {
              toastActions = actions;
            }}
          />
        </ToastProvider>
      );

      act(() => {
        toastActions.addToast({ message: 'First toast', type: 'success' });
        toastActions.addToast({ message: 'Second toast', type: 'error' });
        toastActions.addToast({ message: 'Third toast', type: 'info' });
      });

      await waitFor(() => {
        expect(screen.getByText('First toast')).toBeInTheDocument();
        expect(screen.getByText('Second toast')).toBeInTheDocument();
        expect(screen.getByText('Third toast')).toBeInTheDocument();
      });

      // Toasts should be stacked vertically
      const container = screen.getByText('First toast').closest('.space-y-2');
      expect(container).toBeInTheDocument();
    });

    it('removes specific toast by ID', async () => {
      let toastActions: ReturnType<typeof useToast>;
      let addedToastId: string;

      render(
        <ToastProvider>
          <TestToastConsumer
            onMount={(actions) => {
              toastActions = actions;
            }}
          />
        </ToastProvider>
      );

      act(() => {
        toastActions.addToast({ message: 'Toast 1', type: 'success' });
        toastActions.addToast({ message: 'Toast 2', type: 'info' });
      });

      await waitFor(() => {
        expect(screen.getByText('Toast 1')).toBeInTheDocument();
        expect(screen.getByText('Toast 2')).toBeInTheDocument();
      });

      // Get the ID of the first toast
      addedToastId = toastActions.toasts[0].id;

      act(() => {
        toastActions.removeToast(addedToastId);
      });

      await waitFor(() => {
        expect(screen.queryByText('Toast 1')).not.toBeInTheDocument();
        expect(screen.getByText('Toast 2')).toBeInTheDocument();
      });
    });

    it('clears all toasts', async () => {
      render(
        <ToastProvider>
          <TestToastConsumer />
        </ToastProvider>
      );

      // Add multiple toasts
      fireEvent.click(screen.getByText('Add Toast'));
      fireEvent.click(screen.getByText('Add Toast'));
      fireEvent.click(screen.getByText('Add Toast'));

      await waitFor(() => {
        expect(screen.getByTestId('toast-count')).toHaveTextContent('3');
      });

      // Clear all toasts
      fireEvent.click(screen.getByText('Clear All'));

      await waitFor(() => {
        expect(screen.getByTestId('toast-count')).toHaveTextContent('0');
      });
    });
  });

  describe('Toast Positioning', () => {
    it('positions toast container at top-right', async () => {
      let toastActions: ReturnType<typeof useToast>;

      render(
        <ToastProvider>
          <TestToastConsumer
            onMount={(actions) => {
              toastActions = actions;
            }}
          />
        </ToastProvider>
      );

      act(() => {
        toastActions.addToast({
          message: 'Positioned toast',
          type: 'success',
        });
      });

      await waitFor(() => {
        const container = screen.getByText('Positioned toast').closest('.fixed');
        expect(container).toHaveClass('top-4', 'right-4', 'z-50');
      });
    });

    it('constrains toast width appropriately', async () => {
      let toastActions: ReturnType<typeof useToast>;

      render(
        <ToastProvider>
          <TestToastConsumer
            onMount={(actions) => {
              toastActions = actions;
            }}
          />
        </ToastProvider>
      );

      act(() => {
        toastActions.addToast({
          message: 'Width constrained toast',
          type: 'info',
        });
      });

      await waitFor(() => {
        const toast = screen.getByText('Width constrained toast').closest('div');
        expect(toast).toHaveClass('min-w-80', 'max-w-md');
      });
    });
  });

  describe('Accessibility', () => {
    it('provides proper ARIA labels and roles', async () => {
      let toastActions: ReturnType<typeof useToast>;

      render(
        <ToastProvider>
          <TestToastConsumer
            onMount={(actions) => {
              toastActions = actions;
            }}
          />
        </ToastProvider>
      );

      act(() => {
        toastActions.addToast({
          message: 'Accessible toast',
          type: 'success',
        });
      });

      await waitFor(() => {
        const closeButton = screen.getByRole('button', { name: /close/i });
        expect(closeButton).toBeInTheDocument();
        
        // Should have screen reader text
        expect(screen.getByText('Close')).toHaveClass('sr-only');
      });
    });

    it('supports keyboard interaction for close button', async () => {
      let toastActions: ReturnType<typeof useToast>;

      render(
        <ToastProvider>
          <TestToastConsumer
            onMount={(actions) => {
              toastActions = actions;
            }}
          />
        </ToastProvider>
      );

      act(() => {
        toastActions.addToast({
          message: 'Keyboard accessible toast',
          type: 'info',
          duration: 0,
        });
      });

      await waitFor(() => {
        const closeButton = screen.getByRole('button', { name: /close/i });
        closeButton.focus();
        expect(closeButton).toHaveFocus();
        
        fireEvent.keyDown(closeButton, { key: 'Enter' });
      });

      await waitFor(() => {
        expect(screen.queryByText('Keyboard accessible toast')).not.toBeInTheDocument();
      });
    });

    it('provides focus management', async () => {
      let toastActions: ReturnType<typeof useToast>;

      render(
        <ToastProvider>
          <TestToastConsumer
            onMount={(actions) => {
              toastActions = actions;
            }}
          />
        </ToastProvider>
      );

      act(() => {
        toastActions.addToast({
          message: 'Focus managed toast',
          type: 'warning',
        });
      });

      await waitFor(() => {
        const closeButton = screen.getByRole('button', { name: /close/i });
        expect(closeButton).toHaveClass('focus:outline-none', 'focus:ring-2', 'focus:ring-primary-500');
      });
    });
  });

  describe('useToastActions Hook', () => {
    it('provides convenience methods for all toast types', () => {
      render(
        <ToastProvider>
          <TestToastActions />
        </ToastProvider>
      );

      // All action buttons should be available
      expect(screen.getByText('Success Toast')).toBeInTheDocument();
      expect(screen.getByText('Error Toast')).toBeInTheDocument();
      expect(screen.getByText('Info Toast')).toBeInTheDocument();
      expect(screen.getByText('Warning Toast')).toBeInTheDocument();
    });

    it('accepts custom options for convenience methods', async () => {
      const TestCustomOptions: React.FC = () => {
        const { success } = useToastActions();

        return (
          <button
            onClick={() =>
              success('Custom success', {
                duration: 1000,
                action: {
                  label: 'Custom Action',
                  onClick: () => {},
                },
              })
            }
          >
            Custom Success
          </button>
        );
      };

      render(
        <ToastProvider>
          <TestCustomOptions />
        </ToastProvider>
      );

      fireEvent.click(screen.getByText('Custom Success'));

      await waitFor(() => {
        expect(screen.getByText('Custom success')).toBeInTheDocument();
        expect(screen.getByText('Custom Action')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('handles invalid toast data gracefully', async () => {
      let toastActions: ReturnType<typeof useToast>;

      render(
        <ToastProvider>
          <TestToastConsumer
            onMount={(actions) => {
              toastActions = actions;
            }}
          />
        </ToastProvider>
      );

      // Should not throw error with minimal toast data
      expect(() => {
        act(() => {
          toastActions.addToast({
            message: '',
            type: 'success',
          });
        });
      }).not.toThrow();
    });

    it('generates unique IDs for toasts', async () => {
      let toastActions: ReturnType<typeof useToast>;

      render(
        <ToastProvider>
          <TestToastConsumer
            onMount={(actions) => {
              toastActions = actions;
            }}
          />
        </ToastProvider>
      );

      act(() => {
        toastActions.addToast({ message: 'Toast 1', type: 'success' });
        toastActions.addToast({ message: 'Toast 2', type: 'success' });
      });

      await waitFor(() => {
        const ids = toastActions.toasts.map(toast => toast.id);
        const uniqueIds = new Set(ids);
        expect(uniqueIds.size).toBe(ids.length);
      });
    });
  });
});
/**
 * Comprehensive tests for MessageActions component.
 * 
 * Tests interactive message functionality including:
 * - Copy message functionality with clipboard API
 * - Regenerate response option for assistant messages
 * - Thumbs up/down feedback buttons with state management
 * - Share message functionality
 * - Action visibility based on message type and state
 * - Accessibility compliance for all interactive elements
 * - Error handling for clipboard and sharing operations
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { MessageActions } from '../MessageActions';
import type { ChatMessage } from '@/types/hsaAssistant';

// Mock clipboard API
const mockClipboard = {
  writeText: vi.fn(),
};
Object.assign(navigator, { clipboard: mockClipboard });

// Mock Web Share API
const mockShare = vi.fn();
Object.assign(navigator, { share: mockShare });

describe('MessageActions', () => {
  const mockUserMessage: ChatMessage = {
    id: 'user-msg-1',
    content: 'What are the HSA contribution limits for 2024?',
    role: 'user',
    timestamp: '2024-01-15T10:00:00Z',
    status: 'success',
  };

  const mockAssistantMessage: ChatMessage = {
    id: 'assistant-msg-1',
    content: 'For 2024, the HSA contribution limits are $4,150 for individual coverage and $8,300 for family coverage.',
    role: 'assistant',
    timestamp: '2024-01-15T10:00:05Z',
    confidence_score: 0.92,
    status: 'success',
  };

  const mockLoadingMessage: ChatMessage = {
    id: 'loading-msg-1',
    content: 'Thinking...',
    role: 'assistant',
    timestamp: '2024-01-15T10:00:00Z',
    status: 'sending',
  };

  const mockErrorMessage: ChatMessage = {
    id: 'error-msg-1',
    content: 'Sorry, an error occurred.',
    role: 'assistant',
    timestamp: '2024-01-15T10:00:00Z',
    status: 'error',
    error: 'Network error',
  };

  const mockCallbacks = {
    onCopy: vi.fn(),
    onRegenerate: vi.fn(),
    onFeedback: vi.fn(),
    onShare: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockClipboard.writeText.mockResolvedValue(undefined);
    mockShare.mockResolvedValue(undefined);
  });

  describe('Visibility and Layout', () => {
    it('renders actions for user messages with copy and share buttons', () => {
      render(
        <MessageActions
          message={mockUserMessage}
          onCopy={mockCallbacks.onCopy}
          onShare={mockCallbacks.onShare}
        />
      );

      // Should show copy button
      expect(screen.getByTitle('Copy message')).toBeInTheDocument();
      
      // Should show share button
      expect(screen.getByTitle('Share message')).toBeInTheDocument();
      
      // Should NOT show regenerate or feedback buttons for user messages
      expect(screen.queryByTitle('Regenerate response')).not.toBeInTheDocument();
      expect(screen.queryByTitle('Good response')).not.toBeInTheDocument();
      expect(screen.queryByTitle('Bad response')).not.toBeInTheDocument();
    });

    it('renders full action set for assistant messages', () => {
      render(
        <MessageActions
          message={mockAssistantMessage}
          onCopy={mockCallbacks.onCopy}
          onRegenerate={mockCallbacks.onRegenerate}
          onFeedback={mockCallbacks.onFeedback}
          onShare={mockCallbacks.onShare}
        />
      );

      // Should show all buttons for assistant messages
      expect(screen.getByTitle('Copy message')).toBeInTheDocument();
      expect(screen.getByTitle('Regenerate response')).toBeInTheDocument();
      expect(screen.getByTitle('Good response')).toBeInTheDocument();
      expect(screen.getByTitle('Bad response')).toBeInTheDocument();
      expect(screen.getByTitle('Share message')).toBeInTheDocument();
    });

    it('hides actions for loading messages', () => {
      render(
        <MessageActions
          message={mockLoadingMessage}
          onCopy={mockCallbacks.onCopy}
          onShare={mockCallbacks.onShare}
        />
      );

      // Should not render any actions for loading messages
      expect(screen.queryByTitle('Copy message')).not.toBeInTheDocument();
      expect(screen.queryByTitle('Share message')).not.toBeInTheDocument();
    });

    it('shows copy button but hides feedback for error messages', () => {
      render(
        <MessageActions
          message={mockErrorMessage}
          onCopy={mockCallbacks.onCopy}
          onRegenerate={mockCallbacks.onRegenerate}
          onFeedback={mockCallbacks.onFeedback}
          onShare={mockCallbacks.onShare}
        />
      );

      // Should show copy and regenerate buttons
      expect(screen.getByTitle('Copy message')).toBeInTheDocument();
      expect(screen.getByTitle('Regenerate response')).toBeInTheDocument();
      expect(screen.getByTitle('Share message')).toBeInTheDocument();
      
      // Should NOT show feedback buttons for error messages
      expect(screen.queryByTitle('Good response')).not.toBeInTheDocument();
      expect(screen.queryByTitle('Bad response')).not.toBeInTheDocument();
    });

    it('applies hover-based visibility classes', () => {
      render(
        <MessageActions
          message={mockAssistantMessage}
          onCopy={mockCallbacks.onCopy}
        />
      );

      const actionsContainer = screen.getByTitle('Copy message').closest('.flex');
      expect(actionsContainer).toHaveClass('opacity-0', 'group-hover:opacity-100', 'transition-opacity');
    });
  });

  describe('Copy Functionality', () => {
    it('copies message content to clipboard when copy button is clicked', async () => {
      render(
        <MessageActions
          message={mockUserMessage}
          onCopy={mockCallbacks.onCopy}
        />
      );

      const copyButton = screen.getByTitle('Copy message');
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(mockClipboard.writeText).toHaveBeenCalledWith(mockUserMessage.content);
        expect(mockCallbacks.onCopy).toHaveBeenCalledWith(mockUserMessage.content);
      });
    });

    it('shows success state after successful copy', async () => {
      render(
        <MessageActions
          message={mockUserMessage}
          onCopy={mockCallbacks.onCopy}
        />
      );

      const copyButton = screen.getByTitle('Copy message');
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(screen.getByTitle('Copied!')).toBeInTheDocument();
      });

      // Should apply success styling
      const button = screen.getByTitle('Copied!');
      expect(button).toHaveClass('text-green-600', 'bg-green-50');
    });

    it('resets copy success state after 2 seconds', async () => {
      vi.useFakeTimers();
      
      render(
        <MessageActions
          message={mockUserMessage}
          onCopy={mockCallbacks.onCopy}
        />
      );

      const copyButton = screen.getByTitle('Copy message');
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(screen.getByTitle('Copied!')).toBeInTheDocument();
      });

      // Fast-forward 2 seconds
      vi.advanceTimersByTime(2000);

      await waitFor(() => {
        expect(screen.getByTitle('Copy message')).toBeInTheDocument();
        expect(screen.queryByTitle('Copied!')).not.toBeInTheDocument();
      });

      vi.useRealTimers();
    });

    it('handles clipboard API errors gracefully', async () => {
      mockClipboard.writeText.mockRejectedValue(new Error('Clipboard access denied'));
      
      render(
        <MessageActions
          message={mockUserMessage}
          onCopy={mockCallbacks.onCopy}
        />
      );

      const copyButton = screen.getByTitle('Copy message');
      fireEvent.click(copyButton);

      await waitFor(() => {
        // Should still call onCopy callback as fallback
        expect(mockCallbacks.onCopy).toHaveBeenCalledWith(mockUserMessage.content);
      });
    });

    it('does not copy when disabled', () => {
      render(
        <MessageActions
          message={mockUserMessage}
          onCopy={mockCallbacks.onCopy}
          disabled={true}
        />
      );

      const copyButton = screen.getByTitle('Copy message');
      fireEvent.click(copyButton);

      expect(mockClipboard.writeText).not.toHaveBeenCalled();
      expect(mockCallbacks.onCopy).not.toHaveBeenCalled();
    });
  });

  describe('Regenerate Functionality', () => {
    it('calls onRegenerate with message ID when regenerate button is clicked', () => {
      render(
        <MessageActions
          message={mockAssistantMessage}
          onRegenerate={mockCallbacks.onRegenerate}
        />
      );

      const regenerateButton = screen.getByTitle('Regenerate response');
      fireEvent.click(regenerateButton);

      expect(mockCallbacks.onRegenerate).toHaveBeenCalledWith(mockAssistantMessage.id);
    });

    it('disables regenerate button for error messages', () => {
      render(
        <MessageActions
          message={mockErrorMessage}
          onRegenerate={mockCallbacks.onRegenerate}
        />
      );

      const regenerateButton = screen.getByTitle('Regenerate response');
      expect(regenerateButton).toBeDisabled();
    });

    it('does not regenerate when disabled', () => {
      render(
        <MessageActions
          message={mockAssistantMessage}
          onRegenerate={mockCallbacks.onRegenerate}
          disabled={true}
        />
      );

      const regenerateButton = screen.getByTitle('Regenerate response');
      fireEvent.click(regenerateButton);

      expect(mockCallbacks.onRegenerate).not.toHaveBeenCalled();
    });

    it('does not regenerate when message is loading', () => {
      render(
        <MessageActions
          message={{ ...mockAssistantMessage, status: 'sending' }}
          onRegenerate={mockCallbacks.onRegenerate}
        />
      );

      // Actions should not be visible for loading messages
      expect(screen.queryByTitle('Regenerate response')).not.toBeInTheDocument();
    });
  });

  describe('Feedback Functionality', () => {
    it('provides thumbs up feedback when clicked', () => {
      render(
        <MessageActions
          message={mockAssistantMessage}
          onFeedback={mockCallbacks.onFeedback}
        />
      );

      const thumbsUpButton = screen.getByTitle('Good response');
      fireEvent.click(thumbsUpButton);

      expect(mockCallbacks.onFeedback).toHaveBeenCalledWith(mockAssistantMessage.id, 'up');
    });

    it('provides thumbs down feedback when clicked', () => {
      render(
        <MessageActions
          message={mockAssistantMessage}
          onFeedback={mockCallbacks.onFeedback}
        />
      );

      const thumbsDownButton = screen.getByTitle('Bad response');
      fireEvent.click(thumbsDownButton);

      expect(mockCallbacks.onFeedback).toHaveBeenCalledWith(mockAssistantMessage.id, 'down');
    });

    it('toggles feedback state when same button is clicked twice', () => {
      render(
        <MessageActions
          message={mockAssistantMessage}
          onFeedback={mockCallbacks.onFeedback}
        />
      );

      const thumbsUpButton = screen.getByTitle('Good response');
      
      // Click once - should provide feedback
      fireEvent.click(thumbsUpButton);
      expect(mockCallbacks.onFeedback).toHaveBeenCalledWith(mockAssistantMessage.id, 'up');
      
      // Button should show active state
      expect(thumbsUpButton).toHaveClass('text-green-600', 'bg-green-50');
      
      // Click again - should clear feedback
      fireEvent.click(thumbsUpButton);
      
      // onFeedback should have been called twice total
      expect(mockCallbacks.onFeedback).toHaveBeenCalledTimes(2);
    });

    it('switches between up and down feedback', () => {
      render(
        <MessageActions
          message={mockAssistantMessage}
          onFeedback={mockCallbacks.onFeedback}
        />
      );

      const thumbsUpButton = screen.getByTitle('Good response');
      const thumbsDownButton = screen.getByTitle('Bad response');
      
      // Click thumbs up
      fireEvent.click(thumbsUpButton);
      expect(mockCallbacks.onFeedback).toHaveBeenLastCalledWith(mockAssistantMessage.id, 'up');
      expect(thumbsUpButton).toHaveClass('text-green-600');
      
      // Click thumbs down - should switch
      fireEvent.click(thumbsDownButton);
      expect(mockCallbacks.onFeedback).toHaveBeenLastCalledWith(mockAssistantMessage.id, 'down');
      expect(thumbsDownButton).toHaveClass('text-red-600');
      
      // Thumbs up should no longer be active
      expect(thumbsUpButton).not.toHaveClass('text-green-600');
    });

    it('applies correct styling for active feedback buttons', () => {
      render(
        <MessageActions
          message={mockAssistantMessage}
          onFeedback={mockCallbacks.onFeedback}
        />
      );

      const thumbsUpButton = screen.getByTitle('Good response');
      const thumbsDownButton = screen.getByTitle('Bad response');
      
      // Initially inactive
      expect(thumbsUpButton).toHaveClass('text-gray-400');
      expect(thumbsDownButton).toHaveClass('text-gray-400');
      
      // After clicking thumbs up
      fireEvent.click(thumbsUpButton);
      expect(thumbsUpButton).toHaveClass('text-green-600', 'bg-green-50');
      
      // After clicking thumbs down
      fireEvent.click(thumbsDownButton);
      expect(thumbsDownButton).toHaveClass('text-red-600', 'bg-red-50');
    });

    it('does not provide feedback when disabled', () => {
      render(
        <MessageActions
          message={mockAssistantMessage}
          onFeedback={mockCallbacks.onFeedback}
          disabled={true}
        />
      );

      const thumbsUpButton = screen.getByTitle('Good response');
      fireEvent.click(thumbsUpButton);

      expect(mockCallbacks.onFeedback).not.toHaveBeenCalled();
    });
  });

  describe('Share Functionality', () => {
    it('uses Web Share API when available', async () => {
      render(
        <MessageActions
          message={mockUserMessage}
          onShare={mockCallbacks.onShare}
        />
      );

      const shareButton = screen.getByTitle('Share message');
      fireEvent.click(shareButton);

      await waitFor(() => {
        expect(mockShare).toHaveBeenCalledWith({
          title: 'HSA Assistant Message',
          text: mockUserMessage.content,
        });
        expect(mockCallbacks.onShare).toHaveBeenCalledWith(mockUserMessage.id);
      });
    });

    it('falls back to clipboard when Web Share API is not available', async () => {
      // Remove Web Share API
      delete (navigator as any).share;

      render(
        <MessageActions
          message={mockUserMessage}
          onShare={mockCallbacks.onShare}
        />
      );

      const shareButton = screen.getByTitle('Share message');
      fireEvent.click(shareButton);

      await waitFor(() => {
        expect(mockClipboard.writeText).toHaveBeenCalledWith(mockUserMessage.content);
        expect(mockCallbacks.onShare).toHaveBeenCalledWith(mockUserMessage.id);
      });
    });

    it('handles Web Share API errors gracefully', async () => {
      mockShare.mockRejectedValue(new Error('Share failed'));
      
      render(
        <MessageActions
          message={mockUserMessage}
          onShare={mockCallbacks.onShare}
        />
      );

      const shareButton = screen.getByTitle('Share message');
      fireEvent.click(shareButton);

      // Should not throw error
      await waitFor(() => {
        expect(mockCallbacks.onShare).toHaveBeenCalledWith(mockUserMessage.id);
      });
    });

    it('does not share when disabled', () => {
      render(
        <MessageActions
          message={mockUserMessage}
          onShare={mockCallbacks.onShare}
          disabled={true}
        />
      );

      const shareButton = screen.getByTitle('Share message');
      fireEvent.click(shareButton);

      expect(mockShare).not.toHaveBeenCalled();
      expect(mockCallbacks.onShare).not.toHaveBeenCalled();
    });
  });

  describe('Action Button Styling and Behavior', () => {
    it('applies hover effects to action buttons', () => {
      render(
        <MessageActions
          message={mockAssistantMessage}
          onCopy={mockCallbacks.onCopy}
        />
      );

      const copyButton = screen.getByTitle('Copy message');
      expect(copyButton).toHaveClass('transition-all', 'duration-200', 'ease-in-out');
      expect(copyButton).toHaveClass('hover:text-gray-600', 'hover:bg-gray-50');
    });

    it('applies focus styles for keyboard navigation', () => {
      render(
        <MessageActions
          message={mockAssistantMessage}
          onCopy={mockCallbacks.onCopy}
        />
      );

      const copyButton = screen.getByTitle('Copy message');
      expect(copyButton).toHaveClass('focus:outline-none', 'focus:ring-2', 'focus:ring-primary-500');
    });

    it('disables all buttons when disabled prop is true', () => {
      render(
        <MessageActions
          message={mockAssistantMessage}
          onCopy={mockCallbacks.onCopy}
          onRegenerate={mockCallbacks.onRegenerate}
          onFeedback={mockCallbacks.onFeedback}
          onShare={mockCallbacks.onShare}
          disabled={true}
        />
      );

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toBeDisabled();
        expect(button).toHaveClass('opacity-50', 'cursor-not-allowed');
      });
    });

    it('shows appropriate icons for each action', () => {
      render(
        <MessageActions
          message={mockAssistantMessage}
          onCopy={mockCallbacks.onCopy}
          onRegenerate={mockCallbacks.onRegenerate}
          onFeedback={mockCallbacks.onFeedback}
          onShare={mockCallbacks.onShare}
        />
      );

      // Each button should have an SVG icon
      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button.querySelector('svg')).toBeInTheDocument();
      });
    });
  });

  describe('Conditional Rendering', () => {
    it('only renders actions when corresponding callbacks are provided', () => {
      render(
        <MessageActions
          message={mockAssistantMessage}
          onCopy={mockCallbacks.onCopy}
          // Note: Not providing other callbacks
        />
      );

      // Should only show copy button
      expect(screen.getByTitle('Copy message')).toBeInTheDocument();
      expect(screen.queryByTitle('Regenerate response')).not.toBeInTheDocument();
      expect(screen.queryByTitle('Good response')).not.toBeInTheDocument();
      expect(screen.queryByTitle('Share message')).not.toBeInTheDocument();
    });

    it('renders regenerate only for assistant messages', () => {
      render(
        <MessageActions
          message={mockUserMessage}
          onRegenerate={mockCallbacks.onRegenerate}
        />
      );

      expect(screen.queryByTitle('Regenerate response')).not.toBeInTheDocument();
    });

    it('renders feedback buttons only for successful assistant messages', () => {
      const { rerender } = render(
        <MessageActions
          message={mockAssistantMessage}
          onFeedback={mockCallbacks.onFeedback}
        />
      );

      expect(screen.getByTitle('Good response')).toBeInTheDocument();
      expect(screen.getByTitle('Bad response')).toBeInTheDocument();

      // Should not show for error messages
      rerender(
        <MessageActions
          message={mockErrorMessage}
          onFeedback={mockCallbacks.onFeedback}
        />
      );

      expect(screen.queryByTitle('Good response')).not.toBeInTheDocument();
      expect(screen.queryByTitle('Bad response')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('provides proper ARIA labels for screen readers', () => {
      render(
        <MessageActions
          message={mockAssistantMessage}
          onCopy={mockCallbacks.onCopy}
          onRegenerate={mockCallbacks.onRegenerate}
          onFeedback={mockCallbacks.onFeedback}
          onShare={mockCallbacks.onShare}
        />
      );

      // Each button should have screen reader text
      expect(screen.getByText('Copy message')).toHaveClass('sr-only');
      expect(screen.getByText('Regenerate response')).toHaveClass('sr-only');
      expect(screen.getByText('Good response')).toHaveClass('sr-only');
      expect(screen.getByText('Bad response')).toHaveClass('sr-only');
      expect(screen.getByText('Share message')).toHaveClass('sr-only');
    });

    it('supports keyboard navigation', () => {
      render(
        <MessageActions
          message={mockAssistantMessage}
          onCopy={mockCallbacks.onCopy}
          onFeedback={mockCallbacks.onFeedback}
        />
      );

      const copyButton = screen.getByTitle('Copy message');
      const thumbsUpButton = screen.getByTitle('Good response');
      
      // Should be focusable
      copyButton.focus();
      expect(copyButton).toHaveFocus();
      
      thumbsUpButton.focus();
      expect(thumbsUpButton).toHaveFocus();
    });

    it('works with keyboard activation', () => {
      render(
        <MessageActions
          message={mockAssistantMessage}
          onCopy={mockCallbacks.onCopy}
        />
      );

      const copyButton = screen.getByTitle('Copy message');
      copyButton.focus();
      
      // Simulate Enter key
      fireEvent.keyDown(copyButton, { key: 'Enter', code: 'Enter' });
      
      expect(mockCallbacks.onCopy).toHaveBeenCalled();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className to actions container', () => {
      const customClass = 'custom-actions';
      render(
        <MessageActions
          message={mockAssistantMessage}
          onCopy={mockCallbacks.onCopy}
          className={customClass}
        />
      );

      const actionsContainer = screen.getByTitle('Copy message').closest('.flex');
      expect(actionsContainer).toHaveClass(customClass);
    });

    it('preserves base styling with custom className', () => {
      render(
        <MessageActions
          message={mockAssistantMessage}
          onCopy={mockCallbacks.onCopy}
          className="custom"
        />
      );

      const actionsContainer = screen.getByTitle('Copy message').closest('.flex');
      expect(actionsContainer).toHaveClass('custom', 'flex', 'items-center', 'space-x-1');
    });
  });
});
/**
 * Comprehensive tests for MessageBubble component.
 * 
 * Tests enhanced message display with rich formatting including:
 * - Distinct styling for user vs assistant messages
 * - Professional HSA sales representative styling
 * - Status indicators (typing, processing, delivered)
 * - Message timestamp display with "time ago" format
 * - Avatar display and branding
 * - Confidence score display
 * - HSA bank branding colors
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { MessageBubble } from '../MessageBubble';
import type { ChatMessage } from '@/types/hsaAssistant';

// Mock timers for time ago testing
vi.useFakeTimers();

describe('MessageBubble', () => {
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

  beforeEach(() => {
    vi.clearAllMocks();
    // Set a fixed current time for consistent time ago testing
    vi.setSystemTime(new Date('2024-01-15T10:05:00Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('User Messages', () => {
    it('renders user message with correct styling and layout', () => {
      render(<MessageBubble message={mockUserMessage} />);
      
      const messageContent = screen.getByText(mockUserMessage.content);
      expect(messageContent).toBeInTheDocument();
      
      // Check user message styling
      const messageBubble = messageContent.closest('.rounded-2xl');
      expect(messageBubble).toHaveClass('bg-primary-600', 'text-white', 'rounded-br-md');
      
      // Check right alignment
      const messageContainer = screen.getByText(mockUserMessage.content).closest('.flex');
      expect(messageContainer).toHaveClass('justify-end');
    });

    it('displays user avatar with correct styling', () => {
      render(<MessageBubble message={mockUserMessage} />);
      
      // User avatar should have gray background
      const avatar = document.querySelector('.bg-gray-600');
      expect(avatar).toBeInTheDocument();
      expect(avatar).toHaveClass('w-8', 'h-8', 'rounded-full');
    });

    it('does not display confidence score for user messages', () => {
      render(<MessageBubble message={mockUserMessage} />);
      
      expect(screen.queryByText(/confident/)).not.toBeInTheDocument();
      expect(screen.queryByText(/Confidence:/)).not.toBeInTheDocument();
    });

    it('does not display HSA Assistant label for user messages', () => {
      render(<MessageBubble message={mockUserMessage} />);
      
      expect(screen.queryByText('HSA Assistant')).not.toBeInTheDocument();
    });
  });

  describe('Assistant Messages', () => {
    it('renders assistant message with professional styling', () => {
      render(<MessageBubble message={mockAssistantMessage} />);
      
      const messageContent = screen.getByText(mockAssistantMessage.content);
      expect(messageContent).toBeInTheDocument();
      
      // Check assistant message styling (bank branding colors)
      const messageBubble = messageContent.closest('.rounded-2xl');
      expect(messageBubble).toHaveClass('bg-white', 'border', 'border-gray-200', 'text-gray-900', 'rounded-bl-md');
      
      // Check left alignment
      const messageContainer = screen.getByText(mockAssistantMessage.content).closest('.flex');
      expect(messageContainer).toHaveClass('justify-start');
    });

    it('displays HSA Assistant label with branding colors', () => {
      render(<MessageBubble message={mockAssistantMessage} />);
      
      const assistantLabel = screen.getByText('HSA Assistant');
      expect(assistantLabel).toBeInTheDocument();
      expect(assistantLabel).toHaveClass('text-primary-600', 'font-semibold');
    });

    it('displays professional avatar with HSA branding', () => {
      render(<MessageBubble message={mockAssistantMessage} />);
      
      // Assistant avatar should have primary brand color
      const avatar = document.querySelector('.bg-primary-600');
      expect(avatar).toBeInTheDocument();
      expect(avatar).toHaveClass('w-8', 'h-8', 'rounded-full');
      
      // Should contain lightbulb icon for HSA expertise
      const lightbulbIcon = document.querySelector('svg path[d*="M9.663 17h4.673M12 3v1m6.364"]');
      expect(lightbulbIcon).toBeInTheDocument();
    });

    it('displays confidence score with appropriate styling', () => {
      render(<MessageBubble message={mockAssistantMessage} />);
      
      const confidenceScore = screen.getByText('92% confident');
      expect(confidenceScore).toBeInTheDocument();
      
      // Should have green indicator for high confidence (>= 0.8)
      const confidenceIndicator = document.querySelector('.bg-green-400');
      expect(confidenceIndicator).toBeInTheDocument();
    });

    it('displays different confidence indicators based on score', () => {
      const mediumConfidenceMessage = {
        ...mockAssistantMessage,
        confidence_score: 0.7,
      };
      
      const { rerender } = render(<MessageBubble message={mediumConfidenceMessage} />);
      
      // Medium confidence (0.6-0.8) should show yellow
      let indicator = document.querySelector('.bg-yellow-400');
      expect(indicator).toBeInTheDocument();
      expect(screen.getByText('70% confident')).toBeInTheDocument();
      
      // Low confidence (< 0.6) should show red
      const lowConfidenceMessage = {
        ...mockAssistantMessage,
        confidence_score: 0.4,
      };
      
      rerender(<MessageBubble message={lowConfidenceMessage} />);
      
      indicator = document.querySelector('.bg-red-400');
      expect(indicator).toBeInTheDocument();
      expect(screen.getByText('40% confident')).toBeInTheDocument();
    });
  });

  describe('Status Indicators', () => {
    it('displays sending status with spinner', () => {
      const sendingMessage = {
        ...mockUserMessage,
        status: 'sending' as const,
      };
      
      render(<MessageBubble message={sendingMessage} />);
      
      expect(screen.getByText('Sending...')).toBeInTheDocument();
      
      // Should have spinner animation
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
      expect(spinner).toHaveClass('border-b-2', 'border-primary-600');
    });

    it('displays error status with error icon', () => {
      const errorMessage = {
        ...mockAssistantMessage,
        status: 'error' as const,
        error: 'Network error',
      };
      
      render(<MessageBubble message={errorMessage} />);
      
      expect(screen.getByText('Failed to send')).toBeInTheDocument();
      
      // Check error styling
      const messageBubble = screen.getByText(errorMessage.content).closest('.rounded-2xl');
      expect(messageBubble).toHaveClass('bg-red-50', 'border-red-200', 'text-red-800');
      
      // Should have error icon
      const errorIcon = document.querySelector('svg path[fill-rule="evenodd"][d*="M18 10a8 8 0 11-16 0"]');
      expect(errorIcon).toBeInTheDocument();
    });

    it('applies loading opacity for sending messages', () => {
      const sendingMessage = {
        ...mockUserMessage,
        status: 'sending' as const,
      };
      
      render(<MessageBubble message={sendingMessage} />);
      
      const messageBubble = screen.getByText(sendingMessage.content).closest('.rounded-2xl');
      expect(messageBubble).toHaveClass('opacity-75');
    });

    it('does not display status indicator for successful messages', () => {
      render(<MessageBubble message={mockAssistantMessage} />);
      
      expect(screen.queryByText('Sending...')).not.toBeInTheDocument();
      expect(screen.queryByText('Failed to send')).not.toBeInTheDocument();
    });
  });

  describe('Timestamp Display', () => {
    it('displays "Just now" for messages sent within a minute', () => {
      const recentMessage = {
        ...mockUserMessage,
        timestamp: '2024-01-15T10:04:30Z', // 30 seconds ago
      };
      
      render(<MessageBubble message={recentMessage} />);
      
      expect(screen.getByText('Just now')).toBeInTheDocument();
    });

    it('displays minutes ago for messages sent within an hour', () => {
      const minutesAgoMessage = {
        ...mockUserMessage,
        timestamp: '2024-01-15T09:50:00Z', // 15 minutes ago
      };
      
      render(<MessageBubble message={minutesAgoMessage} />);
      
      expect(screen.getByText('15m ago')).toBeInTheDocument();
    });

    it('displays hours ago for messages sent within a day', () => {
      const hoursAgoMessage = {
        ...mockUserMessage,
        timestamp: '2024-01-15T07:00:00Z', // 3 hours ago
      };
      
      render(<MessageBubble message={hoursAgoMessage} />);
      
      expect(screen.getByText('3h ago')).toBeInTheDocument();
    });

    it('displays days ago for older messages', () => {
      const daysAgoMessage = {
        ...mockUserMessage,
        timestamp: '2024-01-13T10:00:00Z', // 2 days ago
      };
      
      render(<MessageBubble message={daysAgoMessage} />);
      
      expect(screen.getByText('2d ago')).toBeInTheDocument();
    });

    it('positions timestamp correctly for user vs assistant messages', () => {
      const { rerender } = render(<MessageBubble message={mockUserMessage} />);
      
      // User message timestamp should be right-aligned
      let timestamp = screen.getByText('5m ago');
      expect(timestamp.closest('div')).toHaveClass('text-right');
      
      // Assistant message timestamp should be left-aligned
      rerender(<MessageBubble message={mockAssistantMessage} />);
      
      timestamp = screen.getByText('5m ago');
      expect(timestamp.closest('div')).toHaveClass('text-left');
    });
  });

  describe('Avatar Display', () => {
    it('shows avatars by default', () => {
      render(<MessageBubble message={mockAssistantMessage} />);
      
      const avatar = document.querySelector('.bg-primary-600');
      expect(avatar).toBeInTheDocument();
    });

    it('hides avatars when showAvatar is false', () => {
      render(<MessageBubble message={mockAssistantMessage} showAvatar={false} />);
      
      const avatar = document.querySelector('.bg-primary-600');
      expect(avatar).not.toBeInTheDocument();
    });

    it('adjusts layout properly when avatar is hidden', () => {
      render(<MessageBubble message={mockAssistantMessage} showAvatar={false} />);
      
      // Should not have space reserved for avatar
      const container = screen.getByText(mockAssistantMessage.content).closest('.flex');
      expect(container).not.toHaveClass('space-x-3');
    });
  });

  describe('Hover Effects', () => {
    it('applies hover effects for assistant messages', () => {
      render(<MessageBubble message={mockAssistantMessage} />);
      
      const messageContainer = screen.getByText(mockAssistantMessage.content).closest('.group');
      expect(messageContainer).toBeInTheDocument();
      
      const messageBubble = screen.getByText(mockAssistantMessage.content).closest('.rounded-2xl');
      expect(messageBubble).toHaveClass('group-hover:shadow-md');
    });

    it('includes smooth transitions', () => {
      render(<MessageBubble message={mockAssistantMessage} />);
      
      const messageBubble = screen.getByText(mockAssistantMessage.content).closest('.rounded-2xl');
      expect(messageBubble).toHaveClass('transition-all', 'duration-200', 'ease-in-out');
    });
  });

  describe('Custom Content', () => {
    it('renders custom children instead of message content when provided', () => {
      const customContent = <div data-testid="custom-content">Custom rich content</div>;
      
      render(
        <MessageBubble message={mockAssistantMessage}>
          {customContent}
        </MessageBubble>
      );
      
      expect(screen.getByTestId('custom-content')).toBeInTheDocument();
      expect(screen.getByText('Custom rich content')).toBeInTheDocument();
      
      // Original message content should not be rendered
      expect(screen.queryByText(mockAssistantMessage.content)).not.toBeInTheDocument();
    });

    it('preserves all other bubble styling with custom content', () => {
      const customContent = <span>Custom content</span>;
      
      render(
        <MessageBubble message={mockAssistantMessage}>
          {customContent}
        </MessageBubble>
      );
      
      // Should still show HSA Assistant label
      expect(screen.getByText('HSA Assistant')).toBeInTheDocument();
      
      // Should still show confidence score
      expect(screen.getByText('92% confident')).toBeInTheDocument();
      
      // Should still have proper styling
      const messageBubble = screen.getByText('Custom content').closest('.rounded-2xl');
      expect(messageBubble).toHaveClass('bg-white', 'border-gray-200');
    });
  });

  describe('Accessibility', () => {
    it('has proper semantic structure', () => {
      render(<MessageBubble message={mockAssistantMessage} />);
      
      // Should have appropriate roles and structure
      const messageContainer = screen.getByText(mockAssistantMessage.content).closest('.flex');
      expect(messageContainer).toBeInTheDocument();
    });

    it('supports screen readers with proper text content', () => {
      render(<MessageBubble message={mockAssistantMessage} />);
      
      // All text content should be accessible
      expect(screen.getByText('HSA Assistant')).toBeInTheDocument();
      expect(screen.getByText(mockAssistantMessage.content)).toBeInTheDocument();
      expect(screen.getByText('92% confident')).toBeInTheDocument();
      expect(screen.getByText('5m ago')).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('constrains message width appropriately', () => {
      render(<MessageBubble message={mockAssistantMessage} />);
      
      const messageWrapper = screen.getByText(mockAssistantMessage.content).closest('.max-w-\\[85%\\]');
      expect(messageWrapper).toBeInTheDocument();
    });

    it('handles long messages with proper word breaking', () => {
      const longMessage = {
        ...mockAssistantMessage,
        content: 'This is a very long message that should wrap properly and not break the layout of the chat interface even on smaller screens.',
      };
      
      render(<MessageBubble message={longMessage} />);
      
      const messageContent = screen.getByText(longMessage.content);
      const messageBubble = messageContent.closest('.rounded-2xl');
      expect(messageBubble?.querySelector('.break-words')).toBeInTheDocument();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const customClass = 'custom-message-bubble';
      
      render(<MessageBubble message={mockAssistantMessage} className={customClass} />);
      
      const messageContainer = screen.getByText(mockAssistantMessage.content).closest('.flex');
      expect(messageContainer).toHaveClass(customClass);
    });

    it('preserves base classes when custom className is provided', () => {
      const customClass = 'custom-class';
      
      render(<MessageBubble message={mockUserMessage} className={customClass} />);
      
      const messageContainer = screen.getByText(mockUserMessage.content).closest('.flex');
      expect(messageContainer).toHaveClass(customClass, 'w-full', 'mb-6', 'group');
    });
  });

  describe('Edge Cases', () => {
    it('handles missing confidence score gracefully', () => {
      const messageWithoutConfidence = {
        ...mockAssistantMessage,
        confidence_score: undefined,
      };
      
      render(<MessageBubble message={messageWithoutConfidence} />);
      
      expect(screen.getByText(messageWithoutConfidence.content)).toBeInTheDocument();
      expect(screen.queryByText(/confident/)).not.toBeInTheDocument();
    });

    it('handles empty message content', () => {
      const emptyMessage = {
        ...mockUserMessage,
        content: '',
      };
      
      render(<MessageBubble message={emptyMessage} />);
      
      // Should still render the bubble structure
      const messageBubble = document.querySelector('.rounded-2xl');
      expect(messageBubble).toBeInTheDocument();
    });

    it('handles very high confidence scores', () => {
      const highConfidenceMessage = {
        ...mockAssistantMessage,
        confidence_score: 0.99,
      };
      
      render(<MessageBubble message={highConfidenceMessage} />);
      
      expect(screen.getByText('99% confident')).toBeInTheDocument();
      
      // Should still use green indicator for high confidence
      const indicator = document.querySelector('.bg-green-400');
      expect(indicator).toBeInTheDocument();
    });

    it('handles invalid timestamp gracefully', () => {
      const invalidTimestampMessage = {
        ...mockUserMessage,
        timestamp: 'invalid-timestamp',
      };
      
      // Should not throw error
      expect(() => {
        render(<MessageBubble message={invalidTimestampMessage} />);
      }).not.toThrow();
    });
  });
});
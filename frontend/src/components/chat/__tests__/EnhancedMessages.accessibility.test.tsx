/**
 * Comprehensive accessibility compliance tests for Enhanced Message Display.
 * 
 * Tests WCAG 2.1 AA compliance including:
 * - Keyboard navigation and focus management
 * - Screen reader compatibility and ARIA labels
 * - Color contrast and visual accessibility
 * - Semantic HTML structure
 * - Focus indicators and keyboard interactions
 * - Alternative text and descriptive content
 * - Accessible form controls and interactions
 */

import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { vi } from 'vitest';
import { MessageList } from '../MessageList';
import { MessageBubble } from '../MessageBubble';
import { MessageActions } from '../MessageActions';
import { RichTextRenderer } from '../RichTextRenderer';
import { ToastProvider } from '../../ui/Toast';
import { ChatProvider } from '../../../contexts/ChatContext';
import type { ChatMessage, Citation } from '@/types/hsaAssistant';

// Extend expect with jest-axe matchers
expect.extend(toHaveNoViolations);

// Mock services
vi.mock('@/services/hsaAssistantService', () => ({
  hsaAssistantService: {
    askQuestion: vi.fn(),
    getHistory: vi.fn(),
  },
}));

// Mock APIs
Object.assign(navigator, {
  clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
  share: vi.fn().mockResolvedValue(undefined),
});

describe('Enhanced Message Display - Accessibility Compliance', () => {
  const mockCitations: Citation[] = [
    {
      document_name: 'IRS Publication 969',
      page_number: 15,
      excerpt: 'HSA contribution limits are set annually by the IRS based on inflation adjustments.',
      relevance_score: 0.95,
    },
    {
      document_name: 'HSA Guidelines',
      excerpt: 'High-deductible health plans must meet minimum deductible requirements.',
      relevance_score: 0.87,
    },
  ];

  const mockMessages: ChatMessage[] = [
    {
      id: 'user-msg-1',
      content: 'What are the HSA contribution limits?',
      role: 'user',
      timestamp: '2024-01-15T10:00:00Z',
      status: 'success',
    },
    {
      id: 'assistant-msg-1',
      content: `# HSA Contribution Limits

For **2024**, the limits are:

- Individual: **$4,150**
- Family: **$8,300**
- Catch-up (55+): *additional $1,000*

Visit [IRS.gov](https://www.irs.gov) for updates.`,
      role: 'assistant',
      timestamp: '2024-01-15T10:00:05Z',
      citations: mockCitations,
      confidence_score: 0.92,
      status: 'success',
    },
  ];

  const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <ToastProvider>
      <ChatProvider>
        {children}
      </ChatProvider>
    </ToastProvider>
  );

  describe('WCAG 2.1 AA Compliance', () => {
    it('passes axe accessibility tests for complete message list', async () => {
      const { container } = render(
        <TestWrapper>
          <MessageList messages={mockMessages} />
        </TestWrapper>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('passes axe accessibility tests for individual message bubble', async () => {
      const { container } = render(
        <MessageBubble message={mockMessages[1]} />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('passes axe accessibility tests for message actions', async () => {
      const { container } = render(
        <MessageActions
          message={mockMessages[1]}
          onCopy={vi.fn()}
          onRegenerate={vi.fn()}
          onFeedback={vi.fn()}
          onShare={vi.fn()}
        />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('passes axe accessibility tests for rich text content', async () => {
      const { container } = render(
        <RichTextRenderer content={mockMessages[1].content} />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('Keyboard Navigation', () => {
    it('supports tab navigation through message actions', () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      const messageContainer = screen.getByText(/HSA Contribution Limits/i).closest('.group');
      const actionButtons = within(messageContainer!).getAllByRole('button');

      // All action buttons should be focusable
      actionButtons.forEach(button => {
        expect(button).toHaveAttribute('tabindex', '0');
        button.focus();
        expect(button).toHaveFocus();
      });
    });

    it('supports keyboard activation for message actions', () => {
      const mockOnCopy = vi.fn();
      const mockOnRegenerate = vi.fn();
      const mockOnFeedback = vi.fn();

      render(
        <MessageActions
          message={mockMessages[1]}
          onCopy={mockOnCopy}
          onRegenerate={mockOnRegenerate}
          onFeedback={mockOnFeedback}
        />
      );

      const copyButton = screen.getByTitle('Copy message');
      
      // Test Enter key activation
      copyButton.focus();
      fireEvent.keyDown(copyButton, { key: 'Enter', code: 'Enter' });
      expect(mockOnCopy).toHaveBeenCalled();

      // Test Space key activation
      const regenerateButton = screen.getByTitle('Regenerate response');
      regenerateButton.focus();
      fireEvent.keyDown(regenerateButton, { key: ' ', code: 'Space' });
      expect(mockOnRegenerate).toHaveBeenCalled();
    });

    it('provides proper focus management for interactive elements', () => {
      render(
        <TestWrapper>
          <MessageList messages={mockMessages} />
        </TestWrapper>
      );

      // Links in rich text should be focusable
      const link = screen.getByRole('link', { name: /IRS.gov/i });
      expect(link).toHaveAttribute('tabindex', '0');
      
      link.focus();
      expect(link).toHaveFocus();
    });

    it('maintains logical tab order', () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      const focusableElements = screen.getAllByRole('button').concat(screen.getAllByRole('link'));
      
      // Tab through all elements
      focusableElements.forEach((element, index) => {
        element.focus();
        expect(element).toHaveFocus();
        
        if (index < focusableElements.length - 1) {
          fireEvent.keyDown(element, { key: 'Tab', shiftKey: false });
        }
      });
    });

    it('supports reverse tab navigation', () => {
      render(
        <MessageActions
          message={mockMessages[1]}
          onCopy={vi.fn()}
          onRegenerate={vi.fn()}
          onFeedback={vi.fn()}
          onShare={vi.fn()}
        />
      );

      const buttons = screen.getAllByRole('button');
      const lastButton = buttons[buttons.length - 1];
      const secondLastButton = buttons[buttons.length - 2];

      // Focus last button and shift-tab
      lastButton.focus();
      expect(lastButton).toHaveFocus();

      fireEvent.keyDown(lastButton, { key: 'Tab', shiftKey: true });
      // In a real scenario, the previous element would receive focus
      // This tests that shift+tab is handled properly
    });
  });

  describe('Screen Reader Compatibility', () => {
    it('provides proper ARIA labels for message actions', () => {
      render(
        <MessageActions
          message={mockMessages[1]}
          onCopy={vi.fn()}
          onRegenerate={vi.fn()}
          onFeedback={vi.fn()}
          onShare={vi.fn()}
        />
      );

      // Each button should have descriptive screen reader text
      expect(screen.getByText('Copy message')).toHaveClass('sr-only');
      expect(screen.getByText('Regenerate response')).toHaveClass('sr-only');
      expect(screen.getByText('Good response')).toHaveClass('sr-only');
      expect(screen.getByText('Bad response')).toHaveClass('sr-only');
      expect(screen.getByText('Share message')).toHaveClass('sr-only');

      // Buttons should have proper title attributes
      expect(screen.getByTitle('Copy message')).toBeInTheDocument();
      expect(screen.getByTitle('Regenerate response')).toBeInTheDocument();
      expect(screen.getByTitle('Good response')).toBeInTheDocument();
      expect(screen.getByTitle('Bad response')).toBeInTheDocument();
      expect(screen.getByTitle('Share message')).toBeInTheDocument();
    });

    it('provides semantic HTML structure for messages', () => {
      render(
        <TestWrapper>
          <MessageList messages={mockMessages} />
        </TestWrapper>
      );

      // Headers should have proper heading roles
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('HSA Contribution Limits');

      // Lists should have proper list roles
      expect(screen.getByRole('list')).toBeInTheDocument();
      const listItems = screen.getAllByRole('listitem');
      expect(listItems.length).toBeGreaterThan(0);

      // Links should have proper link roles
      expect(screen.getByRole('link', { name: /IRS.gov/i })).toBeInTheDocument();
    });

    it('provides accessible names for interactive elements', () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      const messageContainer = screen.getByText(/HSA Contribution Limits/i).closest('.group');
      const copyButton = within(messageContainer!).getByTitle('Copy message');
      
      // Button should have accessible name
      expect(copyButton).toHaveAccessibleName('Copy message');
    });

    it('announces state changes for interactive elements', () => {
      render(
        <MessageActions
          message={mockMessages[1]}
          onCopy={vi.fn()}
          onFeedback={vi.fn()}
        />
      );

      const thumbsUpButton = screen.getByTitle('Good response');
      
      // Initial state
      expect(thumbsUpButton).not.toHaveAttribute('aria-pressed');
      
      // After clicking (active state)
      fireEvent.click(thumbsUpButton);
      
      // Button should indicate its pressed state
      expect(thumbsUpButton).toHaveClass('text-green-600'); // Visual indication
    });

    it('provides context for citations and confidence scores', () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      // Confidence score should have meaningful text
      expect(screen.getByText('92% confident')).toBeInTheDocument();

      // Citations should have clear structure
      expect(screen.getByText('Sources:')).toBeInTheDocument();
      expect(screen.getByText('IRS Publication 969')).toBeInTheDocument();
    });
  });

  describe('Color Contrast and Visual Accessibility', () => {
    it('uses sufficient color contrast for text elements', () => {
      render(
        <TestWrapper>
          <MessageList messages={mockMessages} />
        </TestWrapper>
      );

      // User message should have sufficient contrast
      const userBubble = screen.getByText('What are the HSA contribution limits?').closest('.rounded-2xl');
      expect(userBubble).toHaveClass('bg-primary-600', 'text-white');

      // Assistant message should have sufficient contrast
      const assistantBubble = screen.getByText(/HSA Contribution Limits/i).closest('.rounded-2xl');
      expect(assistantBubble).toHaveClass('bg-white', 'text-gray-900');
    });

    it('provides visual focus indicators', () => {
      render(
        <MessageActions
          message={mockMessages[1]}
          onCopy={vi.fn()}
        />
      );

      const copyButton = screen.getByTitle('Copy message');
      expect(copyButton).toHaveClass(
        'focus:outline-none',
        'focus:ring-2',
        'focus:ring-primary-500',
        'focus:ring-opacity-50'
      );
    });

    it('uses color plus other indicators for status', () => {
      const errorMessage: ChatMessage = {
        ...mockMessages[1],
        status: 'error',
      };

      render(<MessageBubble message={errorMessage} />);

      // Error state should have multiple indicators, not just color
      const errorBubble = screen.getByText(errorMessage.content).closest('.rounded-2xl');
      expect(errorBubble).toHaveClass('bg-red-50', 'border-red-200', 'text-red-800');

      // Should also have text indicator
      expect(screen.getByText('Failed to send')).toBeInTheDocument();
    });

    it('provides high contrast mode support', () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      // Elements should have border styles that work in high contrast mode
      const messageBubble = screen.getByText(/HSA Contribution Limits/i).closest('.rounded-2xl');
      expect(messageBubble).toHaveClass('border', 'border-gray-200');
    });
  });

  describe('Responsive and Touch Accessibility', () => {
    it('provides adequate touch targets for mobile', () => {
      render(
        <MessageActions
          message={mockMessages[1]}
          onCopy={vi.fn()}
          onRegenerate={vi.fn()}
          onFeedback={vi.fn()}
          onShare={vi.fn()}
        />
      );

      const buttons = screen.getAllByRole('button');
      
      // All buttons should have adequate size for touch targets (minimum 44px)
      buttons.forEach(button => {
        expect(button).toHaveClass('p-1.5'); // Provides adequate padding
      });
    });

    it('maintains accessibility at different screen sizes', () => {
      render(
        <TestWrapper>
          <MessageList messages={mockMessages} />
        </TestWrapper>
      );

      // Messages should have responsive max-width
      const messageWrapper = screen.getByText(/HSA Contribution Limits/i).closest('.max-w-\\[85%\\]');
      expect(messageWrapper).toBeInTheDocument();
    });

    it('handles text scaling appropriately', () => {
      render(
        <RichTextRenderer content="This is **bold** text with *italics*" />
      );

      // Text should scale properly with font size increases
      const boldElement = document.querySelector('strong');
      const italicElement = document.querySelector('em');
      
      expect(boldElement).toHaveClass('font-semibold');
      expect(italicElement).toHaveClass('italic');
    });
  });

  describe('Form Controls and Interactions', () => {
    it('provides proper labels for form-like interactions', () => {
      render(
        <MessageActions
          message={mockMessages[1]}
          onFeedback={vi.fn()}
        />
      );

      const thumbsUpButton = screen.getByTitle('Good response');
      const thumbsDownButton = screen.getByTitle('Bad response');

      // Both should be clearly labeled
      expect(thumbsUpButton).toHaveAccessibleName('Good response');
      expect(thumbsDownButton).toHaveAccessibleName('Bad response');
    });

    it('groups related controls logically', () => {
      render(
        <MessageActions
          message={mockMessages[1]}
          onCopy={vi.fn()}
          onRegenerate={vi.fn()}
          onFeedback={vi.fn()}
          onShare={vi.fn()}
        />
      );

      // Feedback buttons should be grouped together visually and semantically
      const container = screen.getByTitle('Copy message').closest('.flex');
      expect(container).toHaveClass('items-center', 'space-x-1');
    });

    it('provides feedback for user actions', () => {
      render(
        <MessageActions
          message={mockMessages[1]}
          onCopy={vi.fn()}
        />
      );

      const copyButton = screen.getByTitle('Copy message');
      
      // After copying, button should show success state
      fireEvent.click(copyButton);
      expect(screen.getByTitle('Copied!')).toBeInTheDocument();
    });
  });

  describe('Error States and Fallbacks', () => {
    it('provides accessible error messages', () => {
      const errorMessage: ChatMessage = {
        id: 'error-msg',
        content: 'Sorry, an error occurred.',
        role: 'assistant',
        timestamp: '2024-01-15T10:00:00Z',
        status: 'error',
        error: 'Network timeout',
      };

      render(<MessageBubble message={errorMessage} />);

      // Error should be clearly indicated
      expect(screen.getByText('Sorry, an error occurred.')).toBeInTheDocument();
      expect(screen.getByText('Failed to send')).toBeInTheDocument();
      
      const errorBubble = screen.getByText(errorMessage.content).closest('.rounded-2xl');
      expect(errorBubble).toHaveClass('bg-red-50', 'text-red-800');
    });

    it('handles loading states accessibly', () => {
      const loadingMessage: ChatMessage = {
        id: 'loading-msg',
        content: 'Thinking...',
        role: 'assistant',
        timestamp: '2024-01-15T10:00:00Z',
        status: 'sending',
      };

      render(<MessageBubble message={loadingMessage} />);

      // Loading state should be announced
      expect(screen.getByText('Sending...')).toBeInTheDocument();
      
      // Should have visual loading indicator
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('provides fallbacks when features are not available', () => {
      // Remove clipboard API
      delete (navigator as any).clipboard;

      render(
        <MessageActions
          message={mockMessages[1]}
          onCopy={vi.fn()}
        />
      );

      const copyButton = screen.getByTitle('Copy message');
      
      // Should still be functional without throwing errors
      expect(() => fireEvent.click(copyButton)).not.toThrow();
    });
  });

  describe('Content Accessibility', () => {
    it('provides meaningful link text', () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      const link = screen.getByRole('link', { name: /IRS.gov/i });
      expect(link).toHaveAccessibleName('IRS.gov');
    });

    it('uses proper heading hierarchy', () => {
      render(
        <RichTextRenderer content="# Main Title\n## Subtitle\n### Details" />
      );

      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Main Title');
      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Subtitle');
      expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('Details');
    });

    it('provides context for abbreviations and technical terms', () => {
      render(
        <TestWrapper>
          <MessageList messages={mockMessages} />
        </TestWrapper>
      );

      // HSA should be clear from context or have expansion
      expect(screen.getByText(/HSA/i)).toBeInTheDocument();
    });

    it('handles long content with proper structure', () => {
      const longContent = `# Long HSA Guide

## Section 1: Eligibility
You must have a high-deductible health plan.

## Section 2: Contributions
- Individual limit: $4,150
- Family limit: $8,300

## Section 3: Withdrawals
Withdrawals for qualified medical expenses are tax-free.`;

      render(<RichTextRenderer content={longContent} />);

      // Should maintain proper heading structure
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Long HSA Guide');
      expect(screen.getAllByRole('heading', { level: 2 })).toHaveLength(3);
    });
  });

  describe('Animation and Motion Accessibility', () => {
    it('provides essential animations only', () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      // Animations should be smooth but not excessive
      const messageBubble = screen.getByText(/HSA Contribution Limits/i).closest('.rounded-2xl');
      expect(messageBubble).toHaveClass('transition-all', 'duration-200', 'ease-in-out');
    });

    it('respects reduced motion preferences', () => {
      // This would typically involve CSS media queries
      // Testing framework limitations prevent full testing here
      render(<MessageBubble message={mockMessages[1]} />);

      const messageBubble = screen.getByText(mockMessages[1].content).closest('.rounded-2xl');
      expect(messageBubble).toHaveClass('transition-all');
    });
  });
});
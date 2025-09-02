/**
 * Integration tests for Enhanced MessageList with rich formatting components.
 * 
 * Tests the complete message display workflow including:
 * - MessageBubble integration with RichTextRenderer
 * - MessageActions integration with Toast notifications
 * - Collapsible citation sections
 * - Complete user interaction flows
 * - Professional HSA styling integration
 * - Message actions workflow (copy, share, feedback, regenerate)
 * - Citation display and interaction
 * - Rich text formatting in messages
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { vi } from 'vitest';
import { MessageList } from '../MessageList';
import { ToastProvider } from '../../ui/Toast';
import { ChatProvider } from '../../../contexts/ChatContext';
import type { ChatMessage, Citation } from '@/types/hsaAssistant';

// Mock the HSA Assistant service
vi.mock('@/services/hsaAssistantService', () => ({
  hsaAssistantService: {
    askQuestion: vi.fn(),
    getHistory: vi.fn(),
  },
}));

// Mock clipboard API
const mockClipboard = {
  writeText: vi.fn().mockResolvedValue(undefined),
};
Object.assign(navigator, { clipboard: mockClipboard });

// Mock Web Share API
const mockShare = vi.fn().mockResolvedValue(undefined);
Object.assign(navigator, { share: mockShare });

// Mock timers for animations and auto-dismiss
vi.useFakeTimers();

describe('Enhanced MessageList Integration', () => {
  const mockCitations: Citation[] = [
    {
      document_name: 'IRS Publication 969',
      page_number: 15,
      excerpt: 'HSA contribution limits are adjusted annually for inflation and announced in IRS revenue procedures.',
      relevance_score: 0.95,
    },
    {
      document_name: 'HSA Employer Guide',
      page_number: 8,
      excerpt: 'High-deductible health plans must meet minimum deductible requirements to qualify for HSA eligibility.',
      relevance_score: 0.87,
    },
    {
      document_name: 'HSA Banking Regulations',
      excerpt: 'HSA funds can be invested in various financial instruments once minimum balance requirements are met.',
      relevance_score: 0.78,
    },
  ];

  const mockMessages: ChatMessage[] = [
    {
      id: 'user-msg-1',
      content: 'What are the **HSA contribution limits** for 2024?',
      role: 'user',
      timestamp: '2024-01-15T10:00:00Z',
      status: 'success',
    },
    {
      id: 'assistant-msg-1',
      content: `# HSA Contribution Limits 2024

For **2024**, the HSA contribution limits are:

## Individual Coverage
- Maximum contribution: **$4,150**
- Catch-up contribution (55+): *additional $1,000*

## Family Coverage
- Maximum contribution: **$8,300**
- Catch-up contribution applies per individual

**Important:** These limits are set by the IRS and may change annually. Make sure to check current limits before contributing.`,
      role: 'assistant',
      timestamp: '2024-01-15T10:00:05Z',
      citations: mockCitations,
      confidence_score: 0.94,
      status: 'success',
    },
    {
      id: 'user-msg-2',
      content: 'Can I invest HSA funds?',
      role: 'user',
      timestamp: '2024-01-15T10:01:00Z',
      status: 'success',
    },
    {
      id: 'assistant-msg-2',
      content: `Yes, you can invest HSA funds! Here's what you need to know:

1. **Minimum Balance**: Most HSA providers require a minimum cash balance (typically $1,000-$2,000)
2. **Investment Options**: Common options include:
   - Mutual funds
   - ETFs
   - Individual stocks
   - Bonds

3. **Tax Benefits**: Investment gains are tax-free when used for qualified medical expenses

Visit [our investment center](https://bank.com/hsa-investments) for more details.`,
      role: 'assistant',
      timestamp: '2024-01-15T10:01:15Z',
      citations: [mockCitations[2]],
      confidence_score: 0.89,
      status: 'success',
    },
  ];

  const mockErrorMessage: ChatMessage = {
    id: 'error-msg-1',
    content: 'Sorry, I encountered an error processing your request.',
    role: 'assistant',
    timestamp: '2024-01-15T10:02:00Z',
    status: 'error',
    error: 'Network timeout',
  };

  // Wrapper component with all necessary providers
  const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <ToastProvider>
      <ChatProvider>
        {children}
      </ChatProvider>
    </ToastProvider>
  );

  beforeEach(() => {
    vi.clearAllMocks();
    vi.clearAllTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  describe('Rich Text Rendering Integration', () => {
    it('renders rich text formatting in assistant messages', async () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      // Check headers are rendered
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('HSA Contribution Limits 2024');
      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Individual Coverage');

      // Check bold text formatting
      const boldElements = document.querySelectorAll('strong');
      expect(boldElements.length).toBeGreaterThan(0);
      expect(Array.from(boldElements).some(el => el.textContent?.includes('2024'))).toBe(true);

      // Check list formatting
      const lists = document.querySelectorAll('ul, ol');
      expect(lists.length).toBeGreaterThan(0);

      // Check italic formatting
      const italicElements = document.querySelectorAll('em');
      expect(italicElements.length).toBeGreaterThan(0);
    });

    it('renders links with proper attributes in rich text', async () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[3]]} />
        </TestWrapper>
      );

      const link = screen.getByRole('link', { name: /investment center/i });
      expect(link).toHaveAttribute('href', 'https://bank.com/hsa-investments');
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
      expect(link).toHaveClass('text-primary-600', 'underline');
    });

    it('renders user messages with inline formatting only', async () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[0]]} />
        </TestWrapper>
      );

      // User message should have bold formatting but no block elements
      expect(document.querySelector('strong')).toHaveTextContent('HSA contribution limits');
      expect(document.querySelector('h1')).not.toBeInTheDocument();
      expect(document.querySelector('ul')).not.toBeInTheDocument();
    });
  });

  describe('Professional HSA Styling Integration', () => {
    it('displays HSA Assistant branding for assistant messages', async () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      // Check HSA Assistant label with branding
      expect(screen.getByText('HSA Assistant')).toBeInTheDocument();
      expect(screen.getByText('HSA Assistant')).toHaveClass('text-primary-600', 'font-semibold');

      // Check professional avatar
      const avatar = document.querySelector('.bg-primary-600');
      expect(avatar).toBeInTheDocument();
      expect(avatar).toHaveClass('w-8', 'h-8', 'rounded-full');
    });

    it('displays confidence scores with appropriate indicators', async () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      expect(screen.getByText('94% confident')).toBeInTheDocument();
      
      // High confidence should show green indicator
      const indicator = document.querySelector('.bg-green-400');
      expect(indicator).toBeInTheDocument();
    });

    it('applies professional message bubble styling', async () => {
      render(
        <TestWrapper>
          <MessageList messages={mockMessages} />
        </TestWrapper>
      );

      // User messages should have primary brand colors
      const userBubble = screen.getByText(mockMessages[0].content).closest('.rounded-2xl');
      expect(userBubble).toHaveClass('bg-primary-600', 'text-white');

      // Assistant messages should have professional white styling
      const assistantBubble = screen.getByText(/HSA Contribution Limits/i).closest('.rounded-2xl');
      expect(assistantBubble).toHaveClass('bg-white', 'border-gray-200');
    });
  });

  describe('Citation Display Integration', () => {
    it('displays collapsible citations section for assistant messages', async () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      // Check citations section is rendered
      expect(screen.getByText('Sources:')).toBeInTheDocument();
      
      // Should show all citations
      expect(screen.getByText('IRS Publication 969')).toBeInTheDocument();
      expect(screen.getByText('HSA Employer Guide')).toBeInTheDocument();
      expect(screen.getByText('HSA Banking Regulations')).toBeInTheDocument();

      // Citations should display relevance scores
      expect(screen.getByText(/95%/)).toBeInTheDocument();
      expect(screen.getByText(/87%/)).toBeInTheDocument();
      expect(screen.getByText(/78%/)).toBeInTheDocument();
    });

    it('shows page numbers when available in citations', async () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      // Should show page numbers for citations that have them
      expect(screen.getByText(/Page 15/)).toBeInTheDocument();
      expect(screen.getByText(/Page 8/)).toBeInTheDocument();
    });

    it('displays citation excerpts', async () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      // Check that citation excerpts are displayed
      expect(screen.getByText(/contribution limits are adjusted annually/i)).toBeInTheDocument();
      expect(screen.getByText(/minimum deductible requirements/i)).toBeInTheDocument();
      expect(screen.getByText(/invested in various financial instruments/i)).toBeInTheDocument();
    });

    it('does not show citations section when no citations are present', async () => {
      const messageWithoutCitations = {
        ...mockMessages[1],
        citations: [],
      };

      render(
        <TestWrapper>
          <MessageList messages={[messageWithoutCitations]} />
        </TestWrapper>
      );

      expect(screen.queryByText('Sources:')).not.toBeInTheDocument();
    });
  });

  describe('Message Actions Integration', () => {
    it('shows message actions on hover for assistant messages', async () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      // Actions should be present but initially hidden
      const messageContainer = screen.getByText(/HSA Contribution Limits/i).closest('.group');
      expect(messageContainer).toBeInTheDocument();

      // Actions container should have hover-based visibility
      const actionsContainer = document.querySelector('.opacity-0.group-hover\\:opacity-100');
      expect(actionsContainer).toBeInTheDocument();
    });

    it('integrates copy functionality with toast notifications', async () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      const messageContent = screen.getByText(/HSA Contribution Limits/i);
      const messageContainer = messageContent.closest('.group');
      
      // Find copy button (may need to force hover state)
      const copyButton = within(messageContainer!).getByTitle('Copy message');
      fireEvent.click(copyButton);

      // Should copy to clipboard
      await waitFor(() => {
        expect(mockClipboard.writeText).toHaveBeenCalledWith(mockMessages[1].content);
      });

      // Should show toast notification
      await waitFor(() => {
        expect(screen.getByText('Message copied to clipboard')).toBeInTheDocument();
      });
    });

    it('provides regenerate functionality for assistant messages', async () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      const messageContainer = screen.getByText(/HSA Contribution Limits/i).closest('.group');
      const regenerateButton = within(messageContainer!).getByTitle('Regenerate response');
      
      expect(regenerateButton).toBeInTheDocument();
      expect(regenerateButton).not.toBeDisabled();
    });

    it('provides feedback buttons for successful assistant messages', async () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      const messageContainer = screen.getByText(/HSA Contribution Limits/i).closest('.group');
      
      expect(within(messageContainer!).getByTitle('Good response')).toBeInTheDocument();
      expect(within(messageContainer!).getByTitle('Bad response')).toBeInTheDocument();
    });

    it('handles feedback interaction with visual state changes', async () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      const messageContainer = screen.getByText(/HSA Contribution Limits/i).closest('.group');
      const thumbsUpButton = within(messageContainer!).getByTitle('Good response');
      
      // Initially inactive
      expect(thumbsUpButton).toHaveClass('text-gray-400');
      
      // Click feedback
      fireEvent.click(thumbsUpButton);
      
      // Should become active
      expect(thumbsUpButton).toHaveClass('text-green-600');
    });

    it('integrates share functionality', async () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      const messageContainer = screen.getByText(/HSA Contribution Limits/i).closest('.group');
      const shareButton = within(messageContainer!).getByTitle('Share message');
      
      fireEvent.click(shareButton);

      await waitFor(() => {
        expect(mockShare).toHaveBeenCalledWith({
          title: 'HSA Assistant Message',
          text: mockMessages[1].content,
        });
      });
    });
  });

  describe('Error Handling Integration', () => {
    it('displays error messages with appropriate styling and actions', async () => {
      render(
        <TestWrapper>
          <MessageList messages={[mockErrorMessage]} />
        </TestWrapper>
      );

      const errorBubble = screen.getByText(mockErrorMessage.content).closest('.rounded-2xl');
      expect(errorBubble).toHaveClass('bg-red-50', 'border-red-200', 'text-red-800');

      // Should still show copy and regenerate buttons for error messages
      const messageContainer = screen.getByText(mockErrorMessage.content).closest('.group');
      expect(within(messageContainer!).getByTitle('Copy message')).toBeInTheDocument();
      expect(within(messageContainer!).getByTitle('Regenerate response')).toBeInTheDocument();
      
      // Should NOT show feedback buttons for error messages
      expect(within(messageContainer!).queryByTitle('Good response')).not.toBeInTheDocument();
      expect(within(messageContainer!).queryByTitle('Bad response')).not.toBeInTheDocument();
    });

    it('handles copy errors gracefully with toast notifications', async () => {
      mockClipboard.writeText.mockRejectedValueOnce(new Error('Clipboard access denied'));

      render(
        <TestWrapper>
          <MessageList messages={[mockMessages[1]]} />
        </TestWrapper>
      );

      const messageContainer = screen.getByText(/HSA Contribution Limits/i).closest('.group');
      const copyButton = within(messageContainer!).getByTitle('Copy message');
      
      fireEvent.click(copyButton);

      // Should show error toast
      await waitFor(() => {
        expect(screen.getByText('Failed to copy message')).toBeInTheDocument();
      });
    });
  });

  describe('Timestamp Integration', () => {
    it('displays time ago format for all messages', async () => {
      // Set current time for consistent testing
      vi.setSystemTime(new Date('2024-01-15T10:05:00Z'));

      render(
        <TestWrapper>
          <MessageList messages={mockMessages.slice(0, 2)} />
        </TestWrapper>
      );

      // User message (5 minutes ago)
      expect(screen.getByText('5m ago')).toBeInTheDocument();

      // Assistant message (almost 5 minutes ago)
      const timeElements = screen.getAllByText(/ago/);
      expect(timeElements.length).toBe(2);
    });

    it('updates time format appropriately', async () => {
      // Test just now
      vi.setSystemTime(new Date('2024-01-15T10:00:30Z'));

      const recentMessage = {
        ...mockMessages[0],
        timestamp: '2024-01-15T10:00:00Z',
      };

      render(
        <TestWrapper>
          <MessageList messages={[recentMessage]} />
        </TestWrapper>
      );

      expect(screen.getByText('Just now')).toBeInTheDocument();
    });
  });

  describe('Complete User Workflow', () => {
    it('handles complete message interaction workflow', async () => {
      render(
        <TestWrapper>
          <MessageList messages={mockMessages} />
        </TestWrapper>
      );

      // Should render all messages with proper formatting
      expect(screen.getByText(/What are the.*HSA contribution limits/i)).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /HSA Contribution Limits 2024/i })).toBeInTheDocument();
      expect(screen.getByText(/Can I invest HSA funds/i)).toBeInTheDocument();

      // Should show citations for messages that have them
      expect(screen.getAllByText('Sources:')).toHaveLength(2);

      // Should show confidence scores
      expect(screen.getByText('94% confident')).toBeInTheDocument();
      expect(screen.getByText('89% confident')).toBeInTheDocument();

      // Should show HSA Assistant branding
      expect(screen.getAllByText('HSA Assistant')).toHaveLength(2);

      // Should have proper message ordering
      const messages = screen.getAllByText(/ago/);
      expect(messages.length).toBe(4); // One timestamp per message
    });

    it('maintains proper spacing and layout for multiple messages', async () => {
      render(
        <TestWrapper>
          <MessageList messages={mockMessages} />
        </TestWrapper>
      );

      // Messages should be properly spaced
      const messageContainers = document.querySelectorAll('.mb-6');
      expect(messageContainers.length).toBe(4); // One per message

      // User and assistant messages should be properly aligned
      const leftAligned = document.querySelectorAll('.justify-start');
      const rightAligned = document.querySelectorAll('.justify-end');
      
      expect(leftAligned.length).toBe(2); // Assistant messages
      expect(rightAligned.length).toBe(2); // User messages
    });

    it('handles scrolling behavior with multiple enhanced messages', async () => {
      const mockScrollIntoView = vi.fn();
      Element.prototype.scrollIntoView = mockScrollIntoView;

      const { rerender } = render(
        <TestWrapper>
          <MessageList messages={mockMessages.slice(0, 2)} />
        </TestWrapper>
      );

      // Add new message
      rerender(
        <TestWrapper>
          <MessageList messages={mockMessages} />
        </TestWrapper>
      );

      expect(mockScrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth' });
    });
  });

  describe('Performance and Optimization', () => {
    it('handles large numbers of enhanced messages efficiently', async () => {
      const manyMessages: ChatMessage[] = Array.from({ length: 50 }, (_, i) => ({
        id: `msg-${i}`,
        content: `Message ${i} with **rich formatting** and *italics*`,
        role: i % 2 === 0 ? 'user' : 'assistant',
        timestamp: new Date(Date.now() - i * 60000).toISOString(),
        status: 'success' as const,
        ...(i % 2 === 1 && {
          confidence_score: 0.8 + (i % 20) * 0.01,
          citations: i % 5 === 0 ? mockCitations.slice(0, 1) : [],
        }),
      }));

      const startTime = performance.now();
      
      render(
        <TestWrapper>
          <MessageList messages={manyMessages} />
        </TestWrapper>
      );

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render in reasonable time (less than 1 second)
      expect(renderTime).toBeLessThan(1000);

      // Should render all messages
      expect(screen.getAllByText(/Message \d+/).length).toBe(50);
    });

    it('does not cause memory leaks with timers and event listeners', async () => {
      const { unmount } = render(
        <TestWrapper>
          <MessageList messages={mockMessages} />
        </TestWrapper>
      );

      // Add some interactions to create timers
      const messageContainer = screen.getByText(/HSA Contribution Limits/i).closest('.group');
      const copyButton = within(messageContainer!).getByTitle('Copy message');
      fireEvent.click(copyButton);

      // Unmount component
      unmount();

      // Should not have pending timers after unmount
      expect(vi.getTimerCount()).toBe(0);
    });
  });
});
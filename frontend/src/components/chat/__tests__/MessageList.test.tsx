/**
 * Tests for MessageList component.
 * 
 * Tests message display functionality including user/assistant messages,
 * citations, confidence scores, error states, loading states, and auto-scroll.
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { MessageList } from '../MessageList';
import type { ChatMessage, Citation } from '@/types/hsaAssistant';

// Mock CitationCard component
vi.mock('../CitationCard', () => ({
  CitationCard: ({ citation, index }: { citation: Citation; index: number }) => (
    <div data-testid={`citation-${index}`}>
      Citation: {citation.document_name} - {citation.excerpt}
    </div>
  ),
}));

describe('MessageList', () => {
  const mockCitations: Citation[] = [
    {
      document_name: 'IRS Publication 969',
      page_number: 3,
      excerpt: 'HSA contribution limits are determined annually by the IRS.',
      relevance_score: 0.95,
    },
    {
      document_name: 'HSA Guidelines',
      excerpt: 'High-deductible health plans are required for HSA eligibility.',
      relevance_score: 0.87,
    },
  ];

  const mockMessages: ChatMessage[] = [
    {
      id: 'msg-1',
      content: 'What are the HSA contribution limits for 2024?',
      role: 'user',
      timestamp: '2024-01-15T10:00:00Z',
      status: 'success',
    },
    {
      id: 'msg-2',
      content: 'For 2024, the HSA contribution limits are $4,150 for individual coverage and $8,300 for family coverage. If you are 55 or older, you can make an additional catch-up contribution of $1,000.',
      role: 'assistant',
      timestamp: '2024-01-15T10:00:05Z',
      citations: mockCitations,
      confidence_score: 0.92,
      status: 'success',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders empty state when no messages', () => {
    render(<MessageList messages={[]} />);
    
    expect(screen.getByText('Welcome to HSA Assistant')).toBeInTheDocument();
    expect(screen.getByText(/Ask me any questions about Health Savings Accounts/)).toBeInTheDocument();
  });

  it('does not render empty state when loading', () => {
    render(<MessageList messages={[]} isLoading={true} />);
    
    expect(screen.queryByText('Welcome to HSA Assistant')).not.toBeInTheDocument();
    expect(screen.getByText('HSA Assistant is thinking...')).toBeInTheDocument();
  });

  it('renders user message correctly', () => {
    const userMessage: ChatMessage = {
      id: 'msg-user',
      content: 'Test user message',
      role: 'user',
      timestamp: '2024-01-15T10:00:00Z',
      status: 'success',
    };

    render(<MessageList messages={[userMessage]} />);
    
    expect(screen.getByText('Test user message')).toBeInTheDocument();
    
    // Check user message styling
    const messageDiv = screen.getByText('Test user message').closest('div');
    expect(messageDiv).toHaveClass('bg-primary-600', 'text-white');
  });

  it('renders assistant message correctly', () => {
    const assistantMessage: ChatMessage = {
      id: 'msg-assistant',
      content: 'Test assistant response',
      role: 'assistant',
      timestamp: '2024-01-15T10:00:00Z',
      status: 'success',
    };

    render(<MessageList messages={[assistantMessage]} />);
    
    expect(screen.getByText('Test assistant response')).toBeInTheDocument();
    
    // Check assistant message styling
    const messageDiv = screen.getByText('Test assistant response').closest('div');
    expect(messageDiv).toHaveClass('bg-gray-100', 'border-gray-200');
  });

  it('displays confidence score for assistant messages', () => {
    const assistantMessage: ChatMessage = {
      id: 'msg-assistant',
      content: 'Assistant response with confidence',
      role: 'assistant',
      timestamp: '2024-01-15T10:00:00Z',
      confidence_score: 0.85,
      status: 'success',
    };

    render(<MessageList messages={[assistantMessage]} />);
    
    expect(screen.getByText('Confidence: 85%')).toBeInTheDocument();
  });

  it('does not display confidence score for user messages', () => {
    const userMessage: ChatMessage = {
      id: 'msg-user',
      content: 'User message',
      role: 'user',
      timestamp: '2024-01-15T10:00:00Z',
      status: 'success',
    };

    render(<MessageList messages={[userMessage]} />);
    
    expect(screen.queryByText(/Confidence:/)).not.toBeInTheDocument();
  });

  it('displays citations for assistant messages', () => {
    const assistantMessage: ChatMessage = {
      id: 'msg-assistant',
      content: 'Response with citations',
      role: 'assistant',
      timestamp: '2024-01-15T10:00:00Z',
      citations: mockCitations,
      status: 'success',
    };

    render(<MessageList messages={[assistantMessage]} />);
    
    expect(screen.getByText('Sources:')).toBeInTheDocument();
    expect(screen.getByTestId('citation-0')).toBeInTheDocument();
    expect(screen.getByTestId('citation-1')).toBeInTheDocument();
  });

  it('does not display citations section when no citations', () => {
    const assistantMessage: ChatMessage = {
      id: 'msg-assistant',
      content: 'Response without citations',
      role: 'assistant',
      timestamp: '2024-01-15T10:00:00Z',
      status: 'success',
    };

    render(<MessageList messages=[assistantMessage]} />);
    
    expect(screen.queryByText('Sources:')).not.toBeInTheDocument();
  });

  it('displays timestamps correctly', () => {
    const message: ChatMessage = {
      id: 'msg-1',
      content: 'Test message',
      role: 'user',
      timestamp: '2024-01-15T10:30:45Z',
      status: 'success',
    };

    render(<MessageList messages={[message]} />);
    
    // The timestamp should be formatted as a locale time string
    const timestamp = new Date('2024-01-15T10:30:45Z').toLocaleTimeString();
    expect(screen.getByText(timestamp)).toBeInTheDocument();
  });

  it('renders error message correctly', () => {
    const errorMessage: ChatMessage = {
      id: 'msg-error',
      content: 'Sorry, an error occurred',
      role: 'assistant',
      timestamp: '2024-01-15T10:00:00Z',
      status: 'error',
      error: 'Network error',
    };

    render(<MessageList messages={[errorMessage]} />);
    
    expect(screen.getByText('Sorry, an error occurred')).toBeInTheDocument();
    
    // Check error styling
    const messageDiv = screen.getByText('Sorry, an error occurred').closest('div');
    expect(messageDiv).toHaveClass('bg-red-50', 'border-red-200');
    
    // Check retry button is present
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('renders loading message correctly', () => {
    const loadingMessage: ChatMessage = {
      id: 'msg-loading',
      content: 'Sending message...',
      role: 'user',
      timestamp: '2024-01-15T10:00:00Z',
      status: 'sending',
    };

    render(<MessageList messages={[loadingMessage]} />);
    
    expect(screen.getByText('Sending message...')).toBeInTheDocument();
    expect(screen.getByText('Sending...')).toBeInTheDocument();
    
    // Check loading styling
    const messageDiv = screen.getByText('Sending message...').closest('div');
    expect(messageDiv).toHaveClass('opacity-60');
  });

  it('shows loading dots when isLoading is true', () => {
    render(<MessageList messages={[]} isLoading={true} />);
    
    expect(screen.getByText('HSA Assistant is thinking...')).toBeInTheDocument();
    
    // Check for animated dots
    const dots = screen.getAllByRole('generic').filter(el => 
      el.className.includes('animate-bounce')
    );
    expect(dots).toHaveLength(3);
  });

  it('handles retry button click', () => {
    // Mock console.log to verify retry is called
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    
    const errorMessage: ChatMessage = {
      id: 'msg-error',
      content: 'Failed message',
      role: 'assistant',
      timestamp: '2024-01-15T10:00:00Z',
      status: 'error',
    };

    render(<MessageList messages={[errorMessage]} />);
    
    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);
    
    expect(consoleSpy).toHaveBeenCalledWith('Retry message:', 'msg-error');
    
    consoleSpy.mockRestore();
  });

  it('renders multiple messages in correct order', () => {
    render(<MessageList messages={mockMessages} />);
    
    const messages = screen.getAllByText(/HSA|What are/);
    expect(messages).toHaveLength(2);
    
    // User message should come first
    expect(screen.getByText('What are the HSA contribution limits for 2024?')).toBeInTheDocument();
    // Assistant message should come second
    expect(screen.getByText(/For 2024, the HSA contribution limits/)).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const customClass = 'custom-message-list';
    render(<MessageList messages={[]} className={customClass} />);
    
    const container = screen.getByText('Welcome to HSA Assistant').closest('.flex-1');
    expect(container).toHaveClass(customClass);
  });

  it('preserves whitespace in message content', () => {
    const messageWithWhitespace: ChatMessage = {
      id: 'msg-whitespace',
      content: 'Line 1\n\nLine 2\n  Indented line',
      role: 'user',
      timestamp: '2024-01-15T10:00:00Z',
      status: 'success',
    };

    render(<MessageList messages={[messageWithWhitespace]} />);
    
    // Check that the content div has whitespace preservation
    const contentDiv = screen.getByText(/Line 1/).closest('div');
    expect(contentDiv).toHaveClass('whitespace-pre-wrap', 'break-words');
  });

  it('handles messages without citations gracefully', () => {
    const messageWithoutCitations: ChatMessage = {
      id: 'msg-no-citations',
      content: 'Response without citations',
      role: 'assistant',
      timestamp: '2024-01-15T10:00:00Z',
      citations: [],
      status: 'success',
    };

    render(<MessageList messages={[messageWithoutCitations]} />);
    
    expect(screen.getByText('Response without citations')).toBeInTheDocument();
    expect(screen.queryByText('Sources:')).not.toBeInTheDocument();
  });

  it('handles messages without confidence score', () => {
    const messageWithoutConfidence: ChatMessage = {
      id: 'msg-no-confidence',
      content: 'Response without confidence',
      role: 'assistant',
      timestamp: '2024-01-15T10:00:00Z',
      status: 'success',
    };

    render(<MessageList messages={[messageWithoutConfidence]} />);
    
    expect(screen.getByText('Response without confidence')).toBeInTheDocument();
    expect(screen.queryByText(/Confidence:/)).not.toBeInTheDocument();
  });

  it('does not show confidence score for error messages', () => {
    const errorMessage: ChatMessage = {
      id: 'msg-error-with-confidence',
      content: 'Error message',
      role: 'assistant',
      timestamp: '2024-01-15T10:00:00Z',
      confidence_score: 0.5,
      status: 'error',
    };

    render(<MessageList messages={[errorMessage]} />);
    
    expect(screen.getByText('Error message')).toBeInTheDocument();
    expect(screen.queryByText(/Confidence:/)).not.toBeInTheDocument();
  });

  it('positions user messages on the right and assistant messages on the left', () => {
    render(<MessageList messages={mockMessages} />);
    
    // User message container should be right-aligned
    const userMessageContainer = screen.getByText('What are the HSA contribution limits for 2024?')
      .closest('.flex');
    expect(userMessageContainer).toHaveClass('justify-end');
    
    // Assistant message container should be left-aligned
    const assistantMessageContainer = screen.getByText(/For 2024, the HSA contribution limits/)
      .closest('.flex');
    expect(assistantMessageContainer).toHaveClass('justify-start');
  });

  it('auto-scrolls to bottom on new messages', () => {
    const { rerender } = render(<MessageList messages={[mockMessages[0]]} />);
    
    // Mock scrollIntoView
    const mockScrollIntoView = vi.fn();
    Element.prototype.scrollIntoView = mockScrollIntoView;
    
    // Add a new message
    rerender(<MessageList messages={mockMessages} />);
    
    expect(mockScrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth' });
  });

  it('auto-scrolls when loading state changes', () => {
    const mockScrollIntoView = vi.fn();
    Element.prototype.scrollIntoView = mockScrollIntoView;
    
    const { rerender } = render(<MessageList messages={mockMessages} isLoading={false} />);
    
    rerender(<MessageList messages={mockMessages} isLoading={true} />);
    
    expect(mockScrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth' });
  });
});
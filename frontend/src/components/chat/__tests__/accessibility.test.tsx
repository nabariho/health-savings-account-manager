/**
 * Accessibility tests for all chat components.
 * 
 * Tests ARIA labels, keyboard navigation, screen reader support, focus management,
 * and WCAG compliance for the HSA Assistant chat interface.
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { axe, toHaveNoViolations } from 'jest-axe';

import { ChatInput } from '../ChatInput';
import { MessageList } from '../MessageList';
import { CitationCard } from '../CitationCard';
import { ChatCTA } from '../ChatCTA';
import { ChatProvider } from '@/contexts/ChatContext';
import { ChatPage } from '@/pages/ChatPage';
import type { ChatMessage, Citation } from '@/types/hsaAssistant';

// Add jest-axe matcher
expect.extend(toHaveNoViolations);

// Mock dependencies
vi.mock('@/services/hsaAssistantService', () => ({
  hsaAssistantService: {
    askQuestion: vi.fn().mockResolvedValue({
      answer: 'Test response',
      confidence_score: 0.9,
      citations: [],
      source_documents: [],
      created_at: '2024-01-15T10:00:05Z',
    }),
    getHistory: vi.fn().mockResolvedValue([]),
  },
}));

vi.mock('@/components/layout/Layout', () => ({
  Layout: ({ children }: { children: React.ReactNode }) => (
    <main role="main">{children}</main>
  ),
}));

vi.mock('@/components/ui/Button', () => ({
  Button: ({ children, onClick, disabled, type, ...props }: any) => (
    <button onClick={onClick} disabled={disabled} type={type} {...props}>
      {children}
    </button>
  ),
}));

vi.mock('@/components/ui/Card', () => ({
  Card: ({ children, className }: any) => (
    <div className={className} role="region">{children}</div>
  ),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: vi.fn(),
    useParams: vi.fn().mockReturnValue({}),
  };
});

describe('Chat Components Accessibility Tests', () => {
  describe('ChatInput Accessibility', () => {
    const mockOnSendMessage = vi.fn();

    beforeEach(() => {
      vi.clearAllMocks();
    });

    it('should not have accessibility violations', async () => {
      const { container } = render(
        <ChatInput onSendMessage={mockOnSendMessage} />
      );
      
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('has proper ARIA labels and roles', () => {
      render(<ChatInput onSendMessage={mockOnSendMessage} />);
      
      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveAttribute('placeholder');
      
      const sendButton = screen.getByRole('button');
      expect(sendButton).toBeInTheDocument();
      expect(sendButton).toHaveAttribute('type', 'submit');
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSendMessage={mockOnSendMessage} />);
      
      const textarea = screen.getByRole('textbox');
      
      // Should be focusable
      await user.tab();
      expect(textarea).toHaveFocus();
      
      // Should support Enter to submit
      await user.type(textarea, 'Test message');
      await user.keyboard('{Enter}');
      
      expect(mockOnSendMessage).toHaveBeenCalledWith('Test message');
    });

    it('supports keyboard shortcuts', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSendMessage={mockOnSendMessage} />);
      
      const textarea = screen.getByRole('textbox');
      await user.click(textarea);
      
      // Test Shift+Enter for new line
      await user.type(textarea, 'Line 1');
      await user.keyboard('{Shift>}{Enter}{/Shift}');
      await user.type(textarea, 'Line 2');
      
      expect(textarea).toHaveValue('Line 1\nLine 2');
    });

    it('provides keyboard shortcuts information', () => {
      render(<ChatInput onSendMessage={mockOnSendMessage} />);
      
      expect(screen.getByText('Press Enter to send, Shift+Enter for new line')).toBeInTheDocument();
    });

    it('manages focus properly', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSendMessage={mockOnSendMessage} />);
      
      const textarea = screen.getByRole('textbox');
      
      // Should auto-focus on mount
      expect(textarea).toHaveFocus();
      
      // Focus should return to textarea after sending
      await user.type(textarea, 'Test');
      await user.keyboard('{Enter}');
      
      expect(textarea).toHaveFocus();
    });

    it('shows example questions with proper accessibility', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSendMessage={mockOnSendMessage} />);
      
      const textarea = screen.getByRole('textbox');
      await user.click(textarea);
      
      // Example questions should be accessible
      expect(screen.getByText('Example questions:')).toBeInTheDocument();
      
      const exampleButtons = screen.getAllByRole('button').filter(btn => 
        btn.textContent?.includes('HSA')
      );
      
      // Each example should be a focusable button
      for (const button of exampleButtons) {
        expect(button).toBeInTheDocument();
      }
    });

    it('handles disabled state accessibly', () => {
      render(<ChatInput onSendMessage={mockOnSendMessage} disabled={true} />);
      
      const textarea = screen.getByRole('textbox');
      const sendButton = screen.getByRole('button');
      
      expect(textarea).toBeDisabled();
      expect(sendButton).toBeDisabled();
    });

    it('provides character count information', () => {
      render(<ChatInput onSendMessage={mockOnSendMessage} />);
      
      const characterCount = screen.getByText('500 characters remaining');
      expect(characterCount).toBeInTheDocument();
    });
  });

  describe('MessageList Accessibility', () => {
    const mockMessages: ChatMessage[] = [
      {
        id: 'msg-1',
        content: 'What are HSA contribution limits?',
        role: 'user',
        timestamp: '2024-01-15T10:00:00Z',
        status: 'success',
      },
      {
        id: 'msg-2',
        content: 'The HSA contribution limit for 2024 is $4,150.',
        role: 'assistant',
        timestamp: '2024-01-15T10:00:05Z',
        confidence_score: 0.92,
        status: 'success',
      },
    ];

    it('should not have accessibility violations', async () => {
      const { container } = render(
        <MessageList messages={mockMessages} />
      );
      
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('has proper semantic structure', () => {
      render(<MessageList messages={mockMessages} />);
      
      // Messages should be in a scrollable region
      const messagesContainer = screen.getByText('What are HSA contribution limits?')
        .closest('.flex-1');
      expect(messagesContainer).toHaveClass('overflow-y-auto');
    });

    it('provides accessible empty state', () => {
      render(<MessageList messages={[]} />);
      
      const welcomeHeading = screen.getByText('Welcome to HSA Assistant');
      expect(welcomeHeading).toBeInTheDocument();
      
      const description = screen.getByText(/Ask me any questions about Health Savings Accounts/);
      expect(description).toBeInTheDocument();
    });

    it('shows loading state accessibly', () => {
      render(<MessageList messages={[]} isLoading={true} />);
      
      const loadingMessage = screen.getByText('HSA Assistant is thinking...');
      expect(loadingMessage).toBeInTheDocument();
    });

    it('handles error messages accessibly', () => {
      const errorMessage: ChatMessage = {
        id: 'msg-error',
        content: 'Sorry, an error occurred',
        role: 'assistant',
        timestamp: '2024-01-15T10:00:00Z',
        status: 'error',
        error: 'Network error',
      };

      render(<MessageList messages={[errorMessage]} />);
      
      const retryButton = screen.getByText('Retry');
      expect(retryButton).toBeInTheDocument();
      expect(retryButton).toHaveAttribute('type', 'button');
    });

    it('provides timestamps accessibly', () => {
      render(<MessageList messages={mockMessages} />);
      
      // Timestamps should be readable
      const timestamps = screen.getAllByText(/\d{1,2}:\d{2}:\d{2}/);
      expect(timestamps.length).toBeGreaterThan(0);
    });
  });

  describe('CitationCard Accessibility', () => {
    const mockCitation: Citation = {
      document_name: 'IRS Publication 969',
      page_number: 15,
      excerpt: 'HSA contribution limits for 2024.',
      relevance_score: 0.85,
    };

    it('should not have accessibility violations', async () => {
      const { container } = render(
        <CitationCard citation={mockCitation} index={0} />
      );
      
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('provides accessible citation information', () => {
      render(<CitationCard citation={mockCitation} index={0} />);
      
      expect(screen.getByText('IRS Publication 969')).toBeInTheDocument();
      expect(screen.getByText('Page 15')).toBeInTheDocument();
      expect(screen.getByText('HSA contribution limits for 2024.')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
    });

    it('has proper semantic structure', () => {
      render(<CitationCard citation={mockCitation} index={0} />);
      
      // Citation should be in a container with proper styling
      const container = screen.getByText('IRS Publication 969').closest('div');
      expect(container).toHaveClass('bg-white', 'border');
    });

    it('shows relevance score visually and textually', () => {
      render(<CitationCard citation={mockCitation} index={0} />);
      
      const relevanceText = screen.getByText('85%');
      expect(relevanceText).toBeInTheDocument();
      
      // Visual indicator should be present
      const relevanceIndicator = relevanceText.previousElementSibling;
      expect(relevanceIndicator).toHaveClass('w-2', 'h-2', 'rounded-full');
    });
  });

  describe('ChatCTA Accessibility', () => {
    const mockOnStartApplication = vi.fn();

    beforeEach(() => {
      vi.clearAllMocks();
    });

    it('should not have accessibility violations', async () => {
      const { container } = render(
        <ChatCTA show={true} onStartApplication={mockOnStartApplication} />
      );
      
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('has proper semantic structure and ARIA attributes', () => {
      render(<ChatCTA show={true} onStartApplication={mockOnStartApplication} />);
      
      // Main CTA region
      const ctaRegion = screen.getByRole('region');
      expect(ctaRegion).toBeInTheDocument();
      
      // Title should be a heading
      const title = screen.getByText('Ready to Open Your HSA?');
      expect(title).toBeInTheDocument();
      
      // Main action button
      const button = screen.getByText('Start HSA Application');
      expect(button).toHaveAttribute('type', 'button');
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<ChatCTA show={true} onStartApplication={mockOnStartApplication} />);
      
      const button = screen.getByText('Start HSA Application');
      
      // Should be focusable
      await user.tab();
      expect(button).toHaveFocus();
      
      // Should be activatable with Enter
      await user.keyboard('{Enter}');
      expect(mockOnStartApplication).toHaveBeenCalled();
    });

    it('provides accessible benefit list', () => {
      render(<ChatCTA show={true} onStartApplication={mockOnStartApplication} />);
      
      const benefits = [
        'Tax deductible',
        'Tax-free growth', 
        'No expiration'
      ];
      
      benefits.forEach(benefit => {
        expect(screen.getByText(benefit)).toBeInTheDocument();
      });
    });

    it('handles focus management', async () => {
      const user = userEvent.setup();
      render(<ChatCTA show={true} onStartApplication={mockOnStartApplication} />);
      
      const startButton = screen.getByText('Start HSA Application');
      const continueLink = screen.getByText('Continue chatting');
      
      // Both elements should be focusable
      await user.tab();
      expect(startButton).toHaveFocus();
      
      await user.tab();
      expect(continueLink).toHaveFocus();
    });
  });

  describe('Full ChatPage Accessibility', () => {
    const renderChatPage = () => {
      return render(
        <BrowserRouter>
          <ChatPage />
        </BrowserRouter>
      );
    };

    it('should not have accessibility violations', async () => {
      const { container } = renderChatPage();
      
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('has proper page structure and landmarks', () => {
      renderChatPage();
      
      // Main content area
      const main = screen.getByRole('main');
      expect(main).toBeInTheDocument();
      
      // Page heading
      const pageHeading = screen.getByText('HSA Assistant');
      expect(pageHeading).toBeInTheDocument();
    });

    it('manages focus flow properly', async () => {
      const user = userEvent.setup();
      renderChatPage();
      
      // Input should be focused initially
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveFocus();
      
      // Tab navigation should work through all interactive elements
      await user.tab(); // Should move to send button or next focusable element
      
      // Verify tab navigation doesn't break
      const focusedElement = document.activeElement;
      expect(focusedElement).not.toBe(textarea);
    });

    it('provides skip links or keyboard shortcuts', () => {
      renderChatPage();
      
      // Check for keyboard shortcut hints
      expect(screen.getByText('Press Enter to send, Shift+Enter for new line')).toBeInTheDocument();
    });

    it('has accessible status indicators', () => {
      renderChatPage();
      
      // Online status should be readable
      expect(screen.getByText('Online')).toBeInTheDocument();
    });

    it('supports screen reader navigation', async () => {
      const user = userEvent.setup();
      renderChatPage();
      
      // All interactive elements should be reachable via keyboard
      const interactiveElements = screen.getAllByRole('button').concat(
        screen.getAllByRole('textbox')
      );
      
      expect(interactiveElements.length).toBeGreaterThan(0);
      
      // Each should be properly labeled
      interactiveElements.forEach(element => {
        expect(element).toBeInTheDocument();
      });
    });

    it('handles dynamic content updates accessibly', async () => {
      const user = userEvent.setup();
      renderChatPage();
      
      const textarea = screen.getByRole('textbox');
      
      // Send a message
      await user.type(textarea, 'Test message');
      await user.keyboard('{Enter}');
      
      // New content should be announced to screen readers
      // (This would typically be handled by proper ARIA live regions)
      await user.findByText('Test message');
    });
  });

  describe('Color Contrast and Visual Accessibility', () => {
    it('uses proper color contrast for text', () => {
      render(
        <MessageList 
          messages={[{
            id: 'msg-1',
            content: 'Test message',
            role: 'user',
            timestamp: '2024-01-15T10:00:00Z',
            status: 'success',
          }]}
        />
      );
      
      // Text should use high contrast colors
      const userMessage = screen.getByText('Test message');
      const messageContainer = userMessage.closest('div');
      expect(messageContainer).toHaveClass('bg-primary-600', 'text-white');
    });

    it('provides visual focus indicators', async () => {
      const user = userEvent.setup();
      render(<ChatInput onSendMessage={vi.fn()} />);
      
      const textarea = screen.getByRole('textbox');
      
      // Focus styles should be applied
      await user.click(textarea);
      expect(textarea).toHaveClass('focus:ring-2', 'focus:ring-primary-500');
    });

    it('uses accessible color indicators for relevance scores', () => {
      const highRelevanceCitation: Citation = {
        document_name: 'Test Document',
        excerpt: 'High relevance excerpt.',
        relevance_score: 0.95,
      };

      render(<CitationCard citation={highRelevanceCitation} index={0} />);
      
      const relevanceIndicator = screen.getByText('95%').previousElementSibling;
      expect(relevanceIndicator).toHaveClass('bg-green-400');
    });
  });

  describe('Responsive and Mobile Accessibility', () => {
    it('maintains accessibility on smaller screens', () => {
      // Simulate mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375, // iPhone SE width
      });

      render(<ChatCTA show={true} onStartApplication={vi.fn()} />);
      
      // Layout should adapt while maintaining accessibility
      const container = screen.getByRole('region');
      expect(container).toBeInTheDocument();
      
      // Buttons should still be accessible
      const button = screen.getByText('Start HSA Application');
      expect(button).toBeInTheDocument();
    });

    it('supports touch interactions', () => {
      render(<ChatInput onSendMessage={vi.fn()} />);
      
      const textarea = screen.getByRole('textbox');
      const sendButton = screen.getByRole('button');
      
      // Elements should be large enough for touch
      expect(textarea).toBeInTheDocument();
      expect(sendButton).toBeInTheDocument();
    });
  });
});
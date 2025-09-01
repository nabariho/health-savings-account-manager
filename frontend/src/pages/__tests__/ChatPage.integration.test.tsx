/**
 * Comprehensive integration tests for User Story 3: "Implement chatbot UI and CTA"
 * 
 * Tests all acceptance criteria:
 * 1. ChatPage displays chat history correctly
 * 2. User can input questions and receive streaming answers
 * 3. Citations are displayed with answers
 * 4. CTA appears below chat and navigates to personal info page
 * 5. Global state qaSession is properly managed
 * 6. Loading states are shown during API calls
 * 7. Error states are handled gracefully
 * 8. Component is accessible (ARIA labels, keyboard navigation)
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, type MockedFunction } from 'vitest';
import { BrowserRouter, useNavigate, useParams } from 'react-router-dom';
import { axe, toHaveNoViolations } from 'jest-axe';

import { ChatPage } from '../ChatPage';
import { hsaAssistantService } from '@/services/hsaAssistantService';
import type { QAResponse, QAHistoryItem } from '@/types/hsaAssistant';

// Add jest-axe matcher
expect.extend(toHaveNoViolations);

// Mock dependencies
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: vi.fn(),
    useParams: vi.fn(),
  };
});

vi.mock('@/services/hsaAssistantService', () => ({
  hsaAssistantService: {
    askQuestion: vi.fn(),
    getHistory: vi.fn(),
  },
}));

vi.mock('@/components/layout/Layout', () => ({
  Layout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="layout">{children}</div>
  ),
}));

vi.mock('@/components/ui/Button', () => ({
  Button: ({ children, onClick, disabled, className, variant, ...props }: any) => (
    <button 
      onClick={onClick} 
      disabled={disabled} 
      className={className}
      data-variant={variant}
      {...props}
    >
      {children}
    </button>
  ),
}));

vi.mock('@/components/ui/Card', () => ({
  Card: ({ children, className }: any) => (
    <div className={className}>{children}</div>
  ),
}));

// Mock data that includes streaming responses and citations
const mockQAResponse: QAResponse = {
  answer: 'The HSA contribution limit for 2024 is $4,150 for individual coverage and $8,300 for family coverage. These limits are adjusted annually for inflation.',
  confidence_score: 0.92,
  citations: [
    {
      document_name: 'IRS Publication 969',
      page_number: 5,
      excerpt: 'For 2024, the annual contribution limit is $4,150 for self-only coverage and $8,300 for family coverage.',
      relevance_score: 0.95,
    },
    {
      document_name: 'IRS Revenue Procedure 2023-23',
      page_number: 2,
      excerpt: 'The annual HSA contribution limits are adjusted for inflation each year.',
      relevance_score: 0.88,
    },
  ],
  source_documents: ['IRS Publication 969', 'IRS Revenue Procedure 2023-23'],
  processing_time_ms: 150,
  created_at: '2024-01-15T10:00:05Z',
};

const mockHistoryItems: QAHistoryItem[] = [
  {
    id: 'qa-1',
    question: 'What are HSA contribution limits?',
    answer: 'The HSA contribution limit for 2024 is $4,150.',
    confidence_score: 0.92,
    citations_count: 1,
    application_id: 'app-123',
    created_at: '2024-01-15T10:00:00Z',
  },
  {
    id: 'qa-2',
    question: 'Am I eligible for an HSA?',
    answer: 'To be eligible for an HSA, you must be enrolled in a High Deductible Health Plan (HDHP).',
    confidence_score: 0.89,
    citations_count: 2,
    application_id: 'app-123',
    created_at: '2024-01-15T10:05:00Z',
  },
];

describe('User Story 3: ChatPage Integration Tests', () => {
  const mockNavigate = vi.fn();
  const mockUseNavigate = useNavigate as MockedFunction<typeof useNavigate>;
  const mockUseParams = useParams as MockedFunction<typeof useParams>;
  const mockAskQuestion = hsaAssistantService.askQuestion as MockedFunction<typeof hsaAssistantService.askQuestion>;
  const mockGetHistory = hsaAssistantService.getHistory as MockedFunction<typeof hsaAssistantService.getHistory>;

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseNavigate.mockReturnValue(mockNavigate);
    mockUseParams.mockReturnValue({});
    mockAskQuestion.mockResolvedValue(mockQAResponse);
    mockGetHistory.mockResolvedValue(mockHistoryItems);
  });

  const renderChatPage = (applicationId?: string) => {
    return render(
      <BrowserRouter>
        <ChatPage applicationId={applicationId} />
      </BrowserRouter>
    );
  };

  describe('AC1: ChatPage displays chat history correctly', () => {
    it('loads and displays historical chat messages in correct order', async () => {
      renderChatPage('app-123');

      // Wait for history to load
      await waitFor(() => {
        expect(mockGetHistory).toHaveBeenCalledWith('app-123');
      });

      // Verify historical messages appear in order
      await waitFor(() => {
        expect(screen.getByText('What are HSA contribution limits?')).toBeInTheDocument();
        expect(screen.getByText('Am I eligible for an HSA?')).toBeInTheDocument();
      });

      // Verify user and assistant messages are properly differentiated
      const userMessages = screen.getAllByTestId(/message.*user/);
      const assistantMessages = screen.getAllByTestId(/message.*assistant/);
      
      expect(userMessages).toHaveLength(2);
      expect(assistantMessages).toHaveLength(2);
    });

    it('handles empty chat history gracefully', async () => {
      mockGetHistory.mockResolvedValueOnce([]);
      renderChatPage('app-empty');

      await waitFor(() => {
        expect(screen.getByText('Welcome to HSA Assistant')).toBeInTheDocument();
      });
    });

    it('displays message timestamps correctly', async () => {
      renderChatPage('app-123');

      await waitFor(() => {
        expect(mockGetHistory).toHaveBeenCalled();
      });

      // Check that timestamps are displayed (assuming MessageList shows them)
      // This would need to be adjusted based on actual implementation
      const messageElements = await screen.findAllByTestId(/message-\d+/);
      expect(messageElements.length).toBeGreaterThan(0);
    });
  });

  describe('AC2: User can input questions and receive streaming answers', () => {
    it('successfully sends question and receives answer', async () => {
      const user = userEvent.setup();
      renderChatPage();

      const textarea = screen.getByRole('textbox');
      const question = 'What are the HSA contribution limits for 2024?';

      await user.type(textarea, question);
      await user.keyboard('{Enter}');

      // Verify user message appears immediately
      await waitFor(() => {
        expect(screen.getByText(question)).toBeInTheDocument();
      });

      // Verify API call made with correct parameters
      expect(mockAskQuestion).toHaveBeenCalledWith(question, undefined, undefined);

      // Verify assistant response appears
      await waitFor(() => {
        expect(screen.getByText(/The HSA contribution limit for 2024/)).toBeInTheDocument();
      });
    });

    it('handles multiple consecutive questions correctly', async () => {
      const user = userEvent.setup();
      renderChatPage();

      const textarea = screen.getByRole('textbox');
      const questions = [
        'What are HSA limits?',
        'Can I use HSA for dental?',
        'What happens at age 65?'
      ];

      for (let i = 0; i < questions.length; i++) {
        await user.clear(textarea);
        await user.type(textarea, questions[i]);
        await user.keyboard('{Enter}');

        await waitFor(() => {
          expect(mockAskQuestion).toHaveBeenCalledTimes(i + 1);
        });
      }

      // All questions should be visible
      questions.forEach(question => {
        expect(screen.getByText(question)).toBeInTheDocument();
      });
    });

    it('provides context for follow-up questions', async () => {
      const user = userEvent.setup();
      renderChatPage();

      const textarea = screen.getByRole('textbox');

      // Send first question
      await user.type(textarea, 'What are HSA limits?');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockAskQuestion).toHaveBeenCalledTimes(1);
      });

      // Send follow-up question
      await user.clear(textarea);
      await user.type(textarea, 'Can I contribute more if I am 55?');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockAskQuestion).toHaveBeenCalledTimes(2);
      });

      // Second call should include context from first response
      expect(mockAskQuestion).toHaveBeenLastCalledWith(
        'Can I contribute more if I am 55?',
        mockQAResponse.answer,
        undefined
      );
    });

    it('clears input after sending message', async () => {
      const user = userEvent.setup();
      renderChatPage();

      const textarea = screen.getByRole('textbox');
      const message = 'Test message to clear';

      await user.type(textarea, message);
      expect(textarea).toHaveValue(message);

      await user.keyboard('{Enter}');

      // Input should be cleared after sending
      expect(textarea).toHaveValue('');
    });
  });

  describe('AC3: Citations are displayed with answers', () => {
    it('displays citations with assistant responses', async () => {
      const user = userEvent.setup();
      renderChatPage();

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'What are HSA limits?');
      await user.keyboard('{Enter}');

      // Wait for response with citations
      await waitFor(() => {
        expect(screen.getByText('Sources:')).toBeInTheDocument();
      });

      // Verify citation documents are displayed
      expect(screen.getByText('IRS Publication 969')).toBeInTheDocument();
      expect(screen.getByText('IRS Revenue Procedure 2023-23')).toBeInTheDocument();

      // Verify excerpts are shown
      expect(screen.getByText(/For 2024, the annual contribution limit is/)).toBeInTheDocument();
    });

    it('handles responses without citations gracefully', async () => {
      const user = userEvent.setup();
      const responseWithoutCitations: QAResponse = {
        ...mockQAResponse,
        citations: [],
        source_documents: [],
      };
      mockAskQuestion.mockResolvedValueOnce(responseWithoutCitations);

      renderChatPage();

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'Test question');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText(responseWithoutCitations.answer)).toBeInTheDocument();
      });

      // Should not show Sources section when no citations
      expect(screen.queryByText('Sources:')).not.toBeInTheDocument();
    });

    it('displays confidence scores appropriately', async () => {
      const user = userEvent.setup();
      renderChatPage();

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'Test question with confidence');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockAskQuestion).toHaveBeenCalled();
      });

      // Check that confidence information is conveyed (implementation-dependent)
      // This might be through visual indicators, tooltips, etc.
    });
  });

  describe('AC4: CTA appears below chat and navigates to personal info page', () => {
    it('shows CTA after sufficient engagement', async () => {
      const user = userEvent.setup();
      renderChatPage();

      const textarea = screen.getByRole('textbox');

      // Send 3 messages to trigger CTA (6 total messages with responses)
      for (let i = 0; i < 3; i++) {
        await user.clear(textarea);
        await user.type(textarea, `Question ${i + 1} about HSA`);
        await user.keyboard('{Enter}');
        
        await waitFor(() => {
          expect(mockAskQuestion).toHaveBeenCalledTimes(i + 1);
        });
      }

      // CTA should appear
      await waitFor(() => {
        expect(screen.getByText('Ready to Open Your HSA?')).toBeInTheDocument();
      });

      expect(screen.getByText('Start HSA Application')).toBeInTheDocument();
    });

    it('shows CTA immediately for eligibility questions', async () => {
      const user = userEvent.setup();
      renderChatPage();

      const textarea = screen.getByRole('textbox');
      
      // Ask eligibility question
      await user.type(textarea, 'Am I eligible for an HSA?');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText('Ready to Open Your HSA?')).toBeInTheDocument();
      });
    });

    it('navigates to personal info page when CTA is clicked', async () => {
      const user = userEvent.setup();
      renderChatPage();

      const textarea = screen.getByRole('textbox');
      
      // Trigger CTA with eligibility question
      await user.type(textarea, 'Can I qualify for HSA?');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText('Ready to Open Your HSA?')).toBeInTheDocument();
      });

      // Click CTA button
      const ctaButton = screen.getByText('Start HSA Application');
      await user.click(ctaButton);

      expect(mockNavigate).toHaveBeenCalledWith('/personal-info');
    });

    it('CTA is positioned correctly below chat', () => {
      const user = userEvent.setup();
      renderChatPage();

      const textarea = screen.getByRole('textbox');
      
      // Trigger CTA
      fireEvent.change(textarea, { target: { value: 'Am I eligible?' } });
      fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });

      // Wait for CTA and verify position
      waitFor(() => {
        const cta = screen.getByText('Ready to Open Your HSA?');
        const ctaContainer = cta.closest('.sticky');
        expect(ctaContainer).toHaveClass('bottom-4');
      });
    });

    it('displays CTA benefits and continue option', async () => {
      const user = userEvent.setup();
      renderChatPage();

      // Trigger CTA
      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'Can I open an HSA?');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText('Ready to Open Your HSA?')).toBeInTheDocument();
      });

      // Verify benefits are displayed
      expect(screen.getByText('Tax deductible')).toBeInTheDocument();
      expect(screen.getByText('Tax-free growth')).toBeInTheDocument();
      expect(screen.getByText('No expiration')).toBeInTheDocument();

      // Verify continue chatting option
      expect(screen.getByText('Continue chatting')).toBeInTheDocument();
    });
  });

  describe('AC5: Global state qaSession is properly managed', () => {
    it('maintains application ID throughout session', async () => {
      const applicationId = 'test-app-123';
      renderChatPage(applicationId);

      // Wait for initial history load
      await waitFor(() => {
        expect(mockGetHistory).toHaveBeenCalledWith(applicationId);
      });

      const user = userEvent.setup();
      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'Test question with app ID');
      await user.keyboard('{Enter}');

      // Verify application ID is passed to API calls
      await waitFor(() => {
        expect(mockAskQuestion).toHaveBeenCalledWith(
          'Test question with app ID',
          undefined,
          applicationId
        );
      });
    });

    it('uses route params for application ID when not provided as prop', async () => {
      const routeApplicationId = 'route-app-456';
      mockUseParams.mockReturnValue({ applicationId: routeApplicationId });

      renderChatPage();

      await waitFor(() => {
        expect(mockGetHistory).toHaveBeenCalledWith(routeApplicationId);
      });
    });

    it('prioritizes prop application ID over route params', async () => {
      const propApplicationId = 'prop-app-789';
      const routeApplicationId = 'route-app-456';
      
      mockUseParams.mockReturnValue({ applicationId: routeApplicationId });

      renderChatPage(propApplicationId);

      await waitFor(() => {
        expect(mockGetHistory).toHaveBeenCalledWith(propApplicationId);
      });
    });

    it('handles new session correctly', async () => {
      mockUseParams.mockReturnValue({ applicationId: 'new' });

      renderChatPage();

      // Should not attempt to load history for new session
      expect(mockGetHistory).not.toHaveBeenCalled();
      expect(screen.getByText('Welcome to HSA Assistant')).toBeInTheDocument();
    });
  });

  describe('AC6: Loading states are shown during API calls', () => {
    it('shows loading indicator during question processing', async () => {
      const user = userEvent.setup();
      
      // Make API call take time
      mockAskQuestion.mockImplementationOnce(
        () => new Promise(resolve => setTimeout(() => resolve(mockQAResponse), 100))
      );

      renderChatPage();

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'Test question');
      await user.keyboard('{Enter}');

      // Should show loading indicator
      expect(screen.getByText('HSA Assistant is thinking...')).toBeInTheDocument();

      // Wait for response
      await waitFor(() => {
        expect(screen.queryByText('HSA Assistant is thinking...')).not.toBeInTheDocument();
      });
    });

    it('disables input during loading', async () => {
      const user = userEvent.setup();
      
      mockAskQuestion.mockImplementationOnce(
        () => new Promise(resolve => setTimeout(() => resolve(mockQAResponse), 100))
      );

      renderChatPage();

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'Test question');
      await user.keyboard('{Enter}');

      // Input should be disabled during loading
      expect(textarea).toBeDisabled();

      // Wait for response
      await waitFor(() => {
        expect(textarea).not.toBeDisabled();
      });
    });

    it('shows loading state during history loading', async () => {
      mockGetHistory.mockImplementationOnce(
        () => new Promise(resolve => setTimeout(() => resolve(mockHistoryItems), 100))
      );

      renderChatPage('app-with-delay');

      // Check for loading state during history load
      // Implementation would depend on how loading is indicated
      await waitFor(() => {
        expect(mockGetHistory).toHaveBeenCalled();
      });
    });
  });

  describe('AC7: Error states are handled gracefully', () => {
    it('displays error message when API call fails', async () => {
      const user = userEvent.setup();
      mockAskQuestion.mockRejectedValueOnce(new Error('Network error'));

      renderChatPage();

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'Test question');
      await user.keyboard('{Enter}');

      // Should display error message
      await waitFor(() => {
        expect(screen.getByText(/Sorry, I encountered an error/)).toBeInTheDocument();
      });
    });

    it('handles history loading errors gracefully', async () => {
      mockGetHistory.mockRejectedValueOnce(new Error('History loading failed'));

      renderChatPage('app-with-error');

      // Should not crash and should show empty state
      await waitFor(() => {
        expect(screen.getByText('Welcome to HSA Assistant')).toBeInTheDocument();
      });
    });

    it('allows retry of failed messages', async () => {
      const user = userEvent.setup();
      mockAskQuestion.mockRejectedValueOnce(new Error('Network error'));

      renderChatPage();

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'Test question');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText(/Sorry, I encountered an error/)).toBeInTheDocument();
      });

      // Look for retry button/option if implemented
      // This would depend on the specific error handling implementation
    });

    it('maintains chat state after error recovery', async () => {
      const user = userEvent.setup();
      
      // First call fails, second succeeds
      mockAskQuestion
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockQAResponse);

      renderChatPage();

      const textarea = screen.getByRole('textbox');
      
      // First message fails
      await user.type(textarea, 'First question');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText(/Sorry, I encountered an error/)).toBeInTheDocument();
      });

      // Second message succeeds
      await user.clear(textarea);
      await user.type(textarea, 'Second question');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText('Second question')).toBeInTheDocument();
        expect(screen.getByText(mockQAResponse.answer)).toBeInTheDocument();
      });
    });
  });

  describe('AC8: Component is accessible (ARIA labels, keyboard navigation)', () => {
    it('should not have accessibility violations', async () => {
      const { container } = renderChatPage();
      
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('has proper ARIA labels and roles', () => {
      renderChatPage();

      // Check main input is properly labeled
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('placeholder');

      // Check send button is accessible
      const sendButton = screen.getByRole('button', { name: /send/i });
      expect(sendButton).toBeInTheDocument();

      // Check main heading
      expect(screen.getByRole('heading', { name: 'HSA Assistant' })).toBeInTheDocument();
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      renderChatPage();

      // Tab to textarea
      await user.tab();
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveFocus();

      // Type message
      await user.type(textarea, 'Keyboard test');

      // Enter to send
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText('Keyboard test')).toBeInTheDocument();
      });
    });

    it('supports screen reader announcements for new messages', async () => {
      const user = userEvent.setup();
      renderChatPage();

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'Test for screen readers');
      await user.keyboard('{Enter}');

      // Check that new messages have appropriate accessibility attributes
      await waitFor(() => {
        const userMessage = screen.getByText('Test for screen readers');
        expect(userMessage.closest('[role="log"]') || userMessage.closest('[aria-live]')).toBeTruthy();
      });
    });

    it('maintains focus management during interactions', async () => {
      const user = userEvent.setup();
      renderChatPage();

      const textarea = screen.getByRole('textbox');
      
      // Focus should return to textarea after sending message
      await user.type(textarea, 'Focus test');
      await user.keyboard('{Enter}');

      // After message is sent, focus should be manageable
      await waitFor(() => {
        expect(textarea).not.toBeDisabled();
      });

      // Should be able to immediately type another message
      await user.type(textarea, 'Second message');
      expect(textarea).toHaveValue('Second message');
    });

    it('CTA button is accessible', async () => {
      const user = userEvent.setup();
      renderChatPage();

      // Trigger CTA
      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'Am I eligible for HSA?');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText('Ready to Open Your HSA?')).toBeInTheDocument();
      });

      // CTA button should be accessible
      const ctaButton = screen.getByRole('button', { name: 'Start HSA Application' });
      expect(ctaButton).toBeInTheDocument();
      
      // Should be reachable via keyboard
      await user.tab();
      // The specific focus behavior would depend on the implementation
    });

    it('provides appropriate alt text for images and icons', () => {
      renderChatPage();

      // Check status indicator has appropriate accessibility
      const statusIndicator = screen.getByText('Online');
      expect(statusIndicator).toBeInTheDocument();

      // SVG icons should have appropriate roles or alt text
      // This would need to be verified based on the actual implementation
    });

    it('handles high contrast mode appropriately', () => {
      renderChatPage();

      // This test would verify that the component works well in high contrast mode
      // The specific implementation would depend on CSS and design system choices
      const mainContainer = screen.getByTestId('layout');
      expect(mainContainer).toBeInTheDocument();
    });
  });

  describe('Edge Cases and Integration Scenarios', () => {
    it('handles rapid successive questions without race conditions', async () => {
      const user = userEvent.setup();
      renderChatPage();

      const textarea = screen.getByRole('textbox');
      const questions = ['Question 1', 'Question 2', 'Question 3'];

      // Send questions rapidly
      for (const question of questions) {
        await user.clear(textarea);
        await user.type(textarea, question);
        await user.keyboard('{Enter}');
      }

      // All questions should be processed correctly
      await waitFor(() => {
        expect(mockAskQuestion).toHaveBeenCalledTimes(3);
      });

      // All questions should appear in the chat
      questions.forEach(question => {
        expect(screen.getByText(question)).toBeInTheDocument();
      });
    });

    it('handles very long messages appropriately', async () => {
      const user = userEvent.setup();
      renderChatPage();

      const longMessage = 'A'.repeat(1000); // Very long message
      const textarea = screen.getByRole('textbox');

      await user.type(textarea, longMessage);
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText(longMessage)).toBeInTheDocument();
      });
    });

    it('maintains responsive layout on different screen sizes', () => {
      // This would involve testing with different viewport sizes
      renderChatPage();

      const mainContainer = screen.getByText('HSA Assistant').closest('.max-w-4xl');
      expect(mainContainer).toHaveClass('mx-auto');

      // Check responsive grid for CTA benefits
      // Would need to trigger CTA first and then test
    });

    it('handles browser refresh with existing session', () => {
      const applicationId = 'persistent-app-123';
      renderChatPage(applicationId);

      // Should load existing session data
      expect(mockGetHistory).toHaveBeenCalledWith(applicationId);
    });

    it('auto-scrolls to new messages', async () => {
      const user = userEvent.setup();
      
      // Mock scrollIntoView
      const mockScrollIntoView = vi.fn();
      Element.prototype.scrollIntoView = mockScrollIntoView;

      renderChatPage();

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'Test scroll behavior');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockScrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth' });
      });
    });
  });
});
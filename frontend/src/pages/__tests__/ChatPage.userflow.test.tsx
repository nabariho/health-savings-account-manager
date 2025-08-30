/**
 * End-to-end User Flow Tests for User Story 3.
 * 
 * Tests the complete user journey from initial chat interaction 
 * through CTA activation to navigation to personal info page.
 * These tests validate the entire story acceptance criteria as a cohesive flow.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, type MockedFunction } from 'vitest';
import { BrowserRouter, useNavigate, useParams } from 'react-router-dom';
import { act } from '@testing-library/react';

import { ChatPage } from '../ChatPage';
import { hsaAssistantService } from '@/services/hsaAssistantService';
import type { QAResponse, QAHistoryItem } from '@/types/hsaAssistant';

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

// Test data
const createMockResponse = (answer: string, citations: number = 1): QAResponse => ({
  answer,
  confidence_score: 0.90,
  citations: Array(citations).fill(0).map((_, i) => ({
    document_name: `HSA Guide ${i + 1}`,
    page_number: i + 1,
    excerpt: `Sample excerpt ${i + 1} relevant to the answer.`,
    relevance_score: 0.85,
  })),
  source_documents: Array(citations).fill(0).map((_, i) => `HSA Guide ${i + 1}`),
  processing_time_ms: 120,
  created_at: '2024-01-15T10:00:00Z',
});

const eligibilityResponse = createMockResponse(
  'To be eligible for an HSA, you must be enrolled in a High Deductible Health Plan (HDHP), not be enrolled in Medicare, and not be claimed as a dependent on someone else\'s tax return.',
  2
);

const contributionResponse = createMockResponse(
  'For 2024, the HSA contribution limits are $4,150 for individual coverage and $8,300 for family coverage.',
  1
);

const benefitsResponse = createMockResponse(
  'HSA contributions are tax-deductible, growth is tax-free, and withdrawals for qualified medical expenses are not taxed.',
  2
);

describe('User Story 3: Complete Chat to CTA User Flow', () => {
  const mockNavigate = vi.fn();
  const mockUseNavigate = useNavigate as MockedFunction<typeof useNavigate>;
  const mockUseParams = useParams as MockedFunction<typeof useParams>;
  const mockAskQuestion = hsaAssistantService.askQuestion as MockedFunction<typeof hsaAssistantService.askQuestion>;
  const mockGetHistory = hsaAssistantService.getHistory as MockedFunction<typeof hsaAssistantService.getHistory>;

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseNavigate.mockReturnValue(mockNavigate);
    mockUseParams.mockReturnValue({});
    mockGetHistory.mockResolvedValue([]);
  });

  const renderChatPage = (applicationId?: string) => {
    return render(
      <BrowserRouter>
        <ChatPage applicationId={applicationId} />
      </BrowserRouter>
    );
  };

  describe('Flow 1: Eligibility-Driven CTA Activation', () => {
    it('completes full journey from eligibility question to application start', async () => {
      // Setup mock responses
      mockAskQuestion.mockResolvedValueOnce(eligibilityResponse);
      
      const user = userEvent.setup();
      renderChatPage();

      // Step 1: User arrives at chat page
      expect(screen.getByText('HSA Assistant')).toBeInTheDocument();
      expect(screen.getByText('Get answers to your Health Savings Account questions')).toBeInTheDocument();
      expect(screen.getByText('Welcome to HSA Assistant')).toBeInTheDocument();

      // Step 2: User asks about eligibility
      const textarea = screen.getByRole('textbox');
      await act(async () => {
        await user.type(textarea, 'Am I eligible for an HSA?');
        await user.keyboard('{Enter}');
      });

      // Step 3: User message appears immediately
      await waitFor(() => {
        expect(screen.getByText('Am I eligible for an HSA?')).toBeInTheDocument();
      });

      // Step 4: Loading state is shown
      expect(screen.getByText('HSA Assistant is thinking...')).toBeInTheDocument();
      expect(textarea).toBeDisabled();

      // Step 5: Assistant responds with eligibility information
      await waitFor(() => {
        expect(screen.getByText(/To be eligible for an HSA/)).toBeInTheDocument();
      });

      // Step 6: Citations are displayed
      expect(screen.getByText('Sources:')).toBeInTheDocument();
      expect(screen.getByText('HSA Guide 1')).toBeInTheDocument();
      expect(screen.getByText('HSA Guide 2')).toBeInTheDocument();

      // Step 7: CTA appears immediately (eligibility question)
      await waitFor(() => {
        expect(screen.getByText('Ready to Open Your HSA?')).toBeInTheDocument();
      });

      // Step 8: CTA displays benefits and call-to-action
      expect(screen.getByText(/Based on our conversation, it looks like you might be eligible/)).toBeInTheDocument();
      expect(screen.getByText('Tax deductible')).toBeInTheDocument();
      expect(screen.getByText('Tax-free growth')).toBeInTheDocument();
      expect(screen.getByText('No expiration')).toBeInTheDocument();
      expect(screen.getByText('Start HSA Application')).toBeInTheDocument();
      expect(screen.getByText('Continue chatting')).toBeInTheDocument();

      // Step 9: User clicks CTA to start application
      const ctaButton = screen.getByText('Start HSA Application');
      await act(async () => {
        await user.click(ctaButton);
      });

      // Step 10: Navigation to personal info page
      expect(mockNavigate).toHaveBeenCalledWith('/personal-info');

      // Verify API call was made correctly
      expect(mockAskQuestion).toHaveBeenCalledWith('Am I eligible for an HSA?', undefined, undefined);
    });

    it('handles follow-up questions after eligibility question and maintains CTA', async () => {
      mockAskQuestion
        .mockResolvedValueOnce(eligibilityResponse)
        .mockResolvedValueOnce(contributionResponse);
      
      const user = userEvent.setup();
      renderChatPage();

      // Ask eligibility question first
      const textarea = screen.getByRole('textbox');
      await act(async () => {
        await user.type(textarea, 'Can I open an HSA?');
        await user.keyboard('{Enter}');
      });

      // Wait for response and CTA
      await waitFor(() => {
        expect(screen.getByText('Ready to Open Your HSA?')).toBeInTheDocument();
      });

      // Ask follow-up question
      await act(async () => {
        await user.clear(textarea);
        await user.type(textarea, 'What are the contribution limits?');
        await user.keyboard('{Enter}');
      });

      // Wait for second response
      await waitFor(() => {
        expect(screen.getByText(/For 2024, the HSA contribution limits are/)).toBeInTheDocument();
      });

      // CTA should still be visible
      expect(screen.getByText('Ready to Open Your HSA?')).toBeInTheDocument();

      // Follow-up should include context
      expect(mockAskQuestion).toHaveBeenLastCalledWith(
        'What are the contribution limits?',
        eligibilityResponse.answer,
        undefined
      );
    });
  });

  describe('Flow 2: Engagement-Driven CTA Activation', () => {
    it('completes journey through sufficient engagement without eligibility questions', async () => {
      mockAskQuestion
        .mockResolvedValueOnce(contributionResponse)
        .mockResolvedValueOnce(benefitsResponse)
        .mockResolvedValueOnce(createMockResponse('HSAs have no expiration date, unlike FSAs.'));
      
      const user = userEvent.setup();
      renderChatPage();

      const textarea = screen.getByRole('textbox');
      const questions = [
        'What are HSA contribution limits?',
        'What are HSA tax benefits?', 
        'Do HSA funds expire?'
      ];

      // Send 3 questions to trigger engagement-based CTA
      for (let i = 0; i < questions.length; i++) {
        await act(async () => {
          await user.clear(textarea);
          await user.type(textarea, questions[i]);
          await user.keyboard('{Enter}');
        });
        
        await waitFor(() => {
          expect(mockAskQuestion).toHaveBeenCalledTimes(i + 1);
        });
        
        // Wait for response
        await waitFor(() => {
          expect(screen.queryByText('HSA Assistant is thinking...')).not.toBeInTheDocument();
        });
      }

      // After 3 exchanges (6 messages total), CTA should appear
      await waitFor(() => {
        expect(screen.getByText('Ready to Open Your HSA?')).toBeInTheDocument();
      });

      // All questions should be visible
      questions.forEach(question => {
        expect(screen.getByText(question)).toBeInTheDocument();
      });

      // Click CTA
      const ctaButton = screen.getByText('Start HSA Application');
      await act(async () => {
        await user.click(ctaButton);
      });

      expect(mockNavigate).toHaveBeenCalledWith('/personal-info');
    });
  });

  describe('Flow 3: Session Management Throughout Journey', () => {
    it('maintains session state from history load through CTA navigation', async () => {
      const historyItems: QAHistoryItem[] = [
        {
          id: 'hist-1',
          question: 'Previous question about HSA',
          answer: 'Previous answer about HSA eligibility.',
          confidence_score: 0.88,
          citations_count: 1,
          application_id: 'flow-app-123',
          created_at: '2024-01-15T09:00:00Z',
        }
      ];

      mockGetHistory.mockResolvedValueOnce(historyItems);
      mockAskQuestion.mockResolvedValueOnce(eligibilityResponse);

      const user = userEvent.setup();
      renderChatPage('flow-app-123');

      // Wait for history to load
      await waitFor(() => {
        expect(mockGetHistory).toHaveBeenCalledWith('flow-app-123');
      });

      // History should be displayed
      await waitFor(() => {
        expect(screen.getByText('Previous question about HSA')).toBeInTheDocument();
        expect(screen.getByText('Previous answer about HSA eligibility.')).toBeInTheDocument();
      });

      // Send new question
      const textarea = screen.getByRole('textbox');
      await act(async () => {
        await user.type(textarea, 'Can I qualify for an HSA?');
        await user.keyboard('{Enter}');
      });

      // Should include application ID in API call
      await waitFor(() => {
        expect(mockAskQuestion).toHaveBeenCalledWith(
          'Can I qualify for an HSA?',
          'Previous answer about HSA eligibility.', // Context from history
          'flow-app-123'
        );
      });

      // CTA should appear
      await waitFor(() => {
        expect(screen.getByText('Ready to Open Your HSA?')).toBeInTheDocument();
      });

      // Navigate via CTA
      const ctaButton = screen.getByText('Start HSA Application');
      await act(async () => {
        await user.click(ctaButton);
      });

      expect(mockNavigate).toHaveBeenCalledWith('/personal-info');
    });
  });

  describe('Flow 4: Error Handling in User Journey', () => {
    it('recovers from API errors and continues to successful CTA interaction', async () => {
      mockAskQuestion
        .mockRejectedValueOnce(new Error('Network timeout'))
        .mockResolvedValueOnce(eligibilityResponse);

      const user = userEvent.setup();
      renderChatPage();

      const textarea = screen.getByRole('textbox');

      // First question fails
      await act(async () => {
        await user.type(textarea, 'First question fails');
        await user.keyboard('{Enter}');
      });

      // Error message should be displayed
      await waitFor(() => {
        expect(screen.getByText(/Sorry, I encountered an error/)).toBeInTheDocument();
      });

      // User can continue with new question
      await act(async () => {
        await user.clear(textarea);
        await user.type(textarea, 'Am I eligible for HSA?');
        await user.keyboard('{Enter}');
      });

      // Second question succeeds
      await waitFor(() => {
        expect(screen.getByText(/To be eligible for an HSA/)).toBeInTheDocument();
      });

      // CTA should appear
      await waitFor(() => {
        expect(screen.getByText('Ready to Open Your HSA?')).toBeInTheDocument();
      });

      // CTA should work normally
      const ctaButton = screen.getByText('Start HSA Application');
      await act(async () => {
        await user.click(ctaButton);
      });

      expect(mockNavigate).toHaveBeenCalledWith('/personal-info');
    });

    it('handles history loading errors but allows normal flow to proceed', async () => {
      mockGetHistory.mockRejectedValueOnce(new Error('History service unavailable'));
      mockAskQuestion.mockResolvedValueOnce(eligibilityResponse);

      const user = userEvent.setup();
      renderChatPage('error-app-456');

      // Should show empty state despite history error
      await waitFor(() => {
        expect(screen.getByText('Welcome to HSA Assistant')).toBeInTheDocument();
      });

      // User can still interact normally
      const textarea = screen.getByRole('textbox');
      await act(async () => {
        await user.type(textarea, 'Do I qualify for HSA?');
        await user.keyboard('{Enter}');
      });

      // Normal flow continues
      await waitFor(() => {
        expect(screen.getByText(/To be eligible for an HSA/)).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText('Ready to Open Your HSA?')).toBeInTheDocument();
      });

      const ctaButton = screen.getByText('Start HSA Application');
      await act(async () => {
        await user.click(ctaButton);
      });

      expect(mockNavigate).toHaveBeenCalledWith('/personal-info');
    });
  });

  describe('Flow 5: Accessibility Throughout Journey', () => {
    it('maintains accessibility during complete user journey', async () => {
      mockAskQuestion.mockResolvedValueOnce(eligibilityResponse);
      
      const user = userEvent.setup();
      renderChatPage();

      // Verify initial accessibility
      expect(screen.getByRole('textbox')).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'HSA Assistant' })).toBeInTheDocument();

      // Tab to textarea
      await act(async () => {
        await user.tab();
      });

      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveFocus();

      // Type and send via keyboard
      await act(async () => {
        await user.type(textarea, 'Am I eligible for HSA?');
        await user.keyboard('{Enter}');
      });

      // Wait for response
      await waitFor(() => {
        expect(screen.getByText(/To be eligible for an HSA/)).toBeInTheDocument();
      });

      // CTA should be accessible
      await waitFor(() => {
        const ctaButton = screen.getByRole('button', { name: 'Start HSA Application' });
        expect(ctaButton).toBeInTheDocument();
      });

      // Should be able to navigate to CTA via keyboard
      const ctaButton = screen.getByRole('button', { name: 'Start HSA Application' });
      
      // Focus and activate via keyboard
      ctaButton.focus();
      expect(ctaButton).toHaveFocus();

      await act(async () => {
        await user.keyboard('{Enter}');
      });

      expect(mockNavigate).toHaveBeenCalledWith('/personal-info');
    });
  });

  describe('Flow 6: Performance and User Experience', () => {
    it('provides responsive feedback throughout the journey', async () => {
      // Simulate slower API response
      mockAskQuestion.mockImplementationOnce(() => 
        new Promise(resolve => setTimeout(() => resolve(eligibilityResponse), 200))
      );

      const user = userEvent.setup();
      renderChatPage();

      const textarea = screen.getByRole('textbox');

      await act(async () => {
        await user.type(textarea, 'Performance test question');
        await user.keyboard('{Enter}');
      });

      // Immediate feedback
      expect(screen.getByText('Performance test question')).toBeInTheDocument();
      expect(screen.getByText('HSA Assistant is thinking...')).toBeInTheDocument();
      expect(textarea).toBeDisabled();

      // Wait for response
      await waitFor(() => {
        expect(screen.queryByText('HSA Assistant is thinking...')).not.toBeInTheDocument();
        expect(textarea).not.toBeDisabled();
      });

      // Input should be re-enabled and ready for next question
      expect(textarea).toHaveValue('');
      await act(async () => {
        await user.type(textarea, 'Follow-up question');
      });
      expect(textarea).toHaveValue('Follow-up question');
    });

    it('handles rapid interactions gracefully', async () => {
      mockAskQuestion
        .mockResolvedValueOnce(contributionResponse)
        .mockResolvedValueOnce(benefitsResponse);

      const user = userEvent.setup();
      renderChatPage();

      const textarea = screen.getByRole('textbox');

      // Send questions rapidly
      await act(async () => {
        await user.type(textarea, 'Question 1');
        await user.keyboard('{Enter}');
      });

      await act(async () => {
        await user.clear(textarea);
        await user.type(textarea, 'Question 2');
        await user.keyboard('{Enter}');
      });

      // Both should be processed correctly
      await waitFor(() => {
        expect(mockAskQuestion).toHaveBeenCalledTimes(2);
      });

      await waitFor(() => {
        expect(screen.getByText('Question 1')).toBeInTheDocument();
        expect(screen.getByText('Question 2')).toBeInTheDocument();
      });
    });
  });

  describe('Flow 7: Edge Cases in Complete Journey', () => {
    it('handles very long messages in the complete flow', async () => {
      const longMessage = 'This is a very long question about HSA eligibility that contains many details about my specific situation and goes on for quite a while to test how the system handles longer user inputs and whether it affects the overall user experience flow. '.repeat(3);
      
      const longResponse = createMockResponse(longMessage + ' - This is the response to your long question.');
      mockAskQuestion.mockResolvedValueOnce(longResponse);

      const user = userEvent.setup();
      renderChatPage();

      const textarea = screen.getByRole('textbox');
      await act(async () => {
        await user.type(textarea, longMessage);
        await user.keyboard('{Enter}');
      });

      // Long message should be handled properly
      await waitFor(() => {
        expect(screen.getByText(longMessage)).toBeInTheDocument();
      });

      // Long response should also be displayed
      await waitFor(() => {
        expect(screen.getByText(longResponse.answer)).toBeInTheDocument();
      });

      // Should trigger CTA if it contains eligibility keywords
      if (longMessage.toLowerCase().includes('eligible')) {
        await waitFor(() => {
          expect(screen.getByText('Ready to Open Your HSA?')).toBeInTheDocument();
        });
      }
    });

    it('completes flow with mixed eligibility and engagement triggers', async () => {
      mockAskQuestion
        .mockResolvedValueOnce(contributionResponse)
        .mockResolvedValueOnce(eligibilityResponse);

      const user = userEvent.setup();
      renderChatPage();

      const textarea = screen.getByRole('textbox');

      // Send non-eligibility question first
      await act(async () => {
        await user.type(textarea, 'What are contribution limits?');
        await user.keyboard('{Enter}');
      });

      await waitFor(() => {
        expect(screen.getByText(/For 2024, the HSA contribution limits/)).toBeInTheDocument();
      });

      // CTA should not appear yet
      expect(screen.queryByText('Ready to Open Your HSA?')).not.toBeInTheDocument();

      // Then send eligibility question
      await act(async () => {
        await user.clear(textarea);
        await user.type(textarea, 'Am I eligible?');
        await user.keyboard('{Enter}');
      });

      await waitFor(() => {
        expect(screen.getByText(/To be eligible for an HSA/)).toBeInTheDocument();
      });

      // CTA should appear immediately after eligibility question
      await waitFor(() => {
        expect(screen.getByText('Ready to Open Your HSA?')).toBeInTheDocument();
      });

      // Complete flow
      const ctaButton = screen.getByText('Start HSA Application');
      await act(async () => {
        await user.click(ctaButton);
      });

      expect(mockNavigate).toHaveBeenCalledWith('/personal-info');
    });
  });
});
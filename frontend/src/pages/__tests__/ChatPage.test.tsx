/**
 * Integration tests for ChatPage component.
 * 
 * Tests full component integration including chat functionality, navigation,
 * CTA interaction, HSA Assistant integration, and complete user workflows.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, type MockedFunction } from 'vitest';
import { BrowserRouter, useNavigate, useParams } from 'react-router-dom';
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
  Button: ({ children, onClick, disabled, className, ...props }: any) => (
    <button onClick={onClick} disabled={disabled} className={className} {...props}>
      {children}
    </button>
  ),
}));

vi.mock('@/components/ui/Card', () => ({
  Card: ({ children, className }: any) => (
    <div className={className}>{children}</div>
  ),
}));

// Mock data
const mockQAResponse: QAResponse = {
  answer: 'The HSA contribution limit for 2024 is $4,150 for individual coverage and $8,300 for family coverage.',
  confidence_score: 0.92,
  citations: [
    {
      document_name: 'IRS Publication 969',
      page_number: 5,
      excerpt: 'For 2024, the annual contribution limit is $4,150 for self-only coverage.',
      relevance_score: 0.95,
    },
  ],
  source_documents: ['IRS Publication 969'],
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
];

describe('ChatPage Integration Tests', () => {
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

  it('renders ChatPage with all components', () => {
    renderChatPage();

    // Check header elements
    expect(screen.getByText('HSA Assistant')).toBeInTheDocument();
    expect(screen.getByText('Get answers to your Health Savings Account questions')).toBeInTheDocument();
    expect(screen.getByText('Online')).toBeInTheDocument();

    // Check empty state
    expect(screen.getByText('Welcome to HSA Assistant')).toBeInTheDocument();
    expect(screen.getByText(/Ask me any questions about Health Savings Accounts/)).toBeInTheDocument();

    // Check input area
    expect(screen.getByRole('textbox')).toBeInTheDocument();
    expect(screen.getByText('Start HSA Application')).toBeInTheDocument(); // Send button initially disabled, so text shows
  });

  it('handles complete question and answer flow', async () => {
    const user = userEvent.setup();
    renderChatPage();

    const textarea = screen.getByRole('textbox');
    const question = 'What are the HSA contribution limits for 2024?';

    // Type question
    await user.type(textarea, question);

    // Send question
    await user.keyboard('{Enter}');

    // Wait for API call and response
    await waitFor(() => {
      expect(screen.getByText(question)).toBeInTheDocument(); // User message
    });

    await waitFor(() => {
      expect(screen.getByText(/The HSA contribution limit for 2024/)).toBeInTheDocument(); // Assistant response
    });

    // Verify API was called correctly
    expect(mockAskQuestion).toHaveBeenCalledWith(question, undefined, undefined);

    // Check citations are displayed
    expect(screen.getByText('Sources:')).toBeInTheDocument();
    expect(screen.getByText('IRS Publication 969')).toBeInTheDocument();
  });

  it('shows CTA after sufficient engagement', async () => {
    const user = userEvent.setup();
    renderChatPage();

    const textarea = screen.getByRole('textbox');

    // Send multiple messages to trigger CTA
    for (let i = 0; i < 3; i++) {
      await user.clear(textarea);
      await user.type(textarea, `Question ${i + 1} about HSA`);
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(mockAskQuestion).toHaveBeenCalledTimes(i + 1);
      });
    }

    // CTA should appear after 6 messages (3 user + 3 assistant)
    await waitFor(() => {
      expect(screen.getByText('Ready to Open Your HSA?')).toBeInTheDocument();
    });
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
    
    // Ask eligibility question to trigger CTA
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

  it('loads history when application ID is provided', async () => {
    const applicationId = 'app-123';
    renderChatPage(applicationId);

    await waitFor(() => {
      expect(mockGetHistory).toHaveBeenCalledWith(applicationId);
    });

    // History messages should be displayed
    await waitFor(() => {
      expect(screen.getByText('What are HSA contribution limits?')).toBeInTheDocument();
    });
  });

  it('uses application ID from route params', async () => {
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

  it('handles API errors gracefully', async () => {
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

    // Should not crash and should still show empty state
    await waitFor(() => {
      expect(screen.getByText('Welcome to HSA Assistant')).toBeInTheDocument();
    });
  });

  it('shows loading state during API calls', async () => {
    const user = userEvent.setup();
    
    // Make API call take longer
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
    
    // Make API call take longer
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

  it('includes application ID in API calls when set', async () => {
    const user = userEvent.setup();
    const applicationId = 'test-app-123';
    renderChatPage(applicationId);

    // Wait for history to load first
    await waitFor(() => {
      expect(mockGetHistory).toHaveBeenCalledWith(applicationId);
    });

    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'Test question with app ID');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(mockAskQuestion).toHaveBeenCalledWith(
        'Test question with app ID',
        undefined,
        applicationId
      );
    });
  });

  it('handles example question selection', async () => {
    const user = userEvent.setup();
    renderChatPage();

    const textarea = screen.getByRole('textbox');
    
    // Focus input to show examples
    await user.click(textarea);

    // Select an example question
    const exampleQuestion = screen.getByText('What are the HSA contribution limits for 2024?');
    await user.click(exampleQuestion);

    // Question should be filled in
    expect(textarea).toHaveValue('What are the HSA contribution limits for 2024?');

    // Send the question
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(mockAskQuestion).toHaveBeenCalledWith(
        'What are the HSA contribution limits for 2024?',
        undefined,
        undefined
      );
    });
  });

  it('maintains responsive layout', () => {
    renderChatPage();

    // Check main container has responsive classes
    const mainContainer = screen.getByText('HSA Assistant').closest('.max-w-4xl');
    expect(mainContainer).toHaveClass('mx-auto');

    // Check header has responsive padding
    const header = screen.getByText('HSA Assistant').closest('.px-4');
    expect(header).toHaveClass('py-4');
  });

  it('shows status indicator', () => {
    renderChatPage();

    // Check online status
    expect(screen.getByText('Online')).toBeInTheDocument();
    
    // Check status indicator dot
    const statusDot = screen.getByText('Online').previousElementSibling;
    expect(statusDot).toHaveClass('w-2', 'h-2', 'bg-green-400', 'rounded-full');
  });

  it('handles accessibility features', () => {
    renderChatPage();

    // Check main input is properly labeled
    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('placeholder', 'Ask me anything about HSA rules, eligibility, or benefits...');

    // Check send button is accessible
    const sendButton = screen.getByRole('button', { name: /send/i });
    expect(sendButton).toBeInTheDocument();
  });

  it('auto-scrolls to new messages', async () => {
    const user = userEvent.setup();
    
    // Mock scrollIntoView
    const mockScrollIntoView = vi.fn();
    Element.prototype.scrollIntoView = mockScrollIntoView;

    renderChatPage();

    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'Test question for scroll');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(mockScrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth' });
    });
  });

  it('handles new session (applicationId = "new")', async () => {
    mockUseParams.mockReturnValue({ applicationId: 'new' });

    renderChatPage();

    // Should not attempt to load history for new session
    expect(mockGetHistory).not.toHaveBeenCalled();

    // Should still show empty state
    expect(screen.getByText('Welcome to HSA Assistant')).toBeInTheDocument();
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
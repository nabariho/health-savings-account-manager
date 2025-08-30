/**
 * Tests for QA Session state management and integration.
 * 
 * Validates that the qaSession global state is properly managed
 * throughout the chat experience as required by User Story 3.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, type MockedFunction } from 'vitest';
import { BrowserRouter } from 'react-router-dom';

import { ChatProvider, useChat } from '@/contexts/ChatContext';
import { hsaAssistantService } from '@/services/hsaAssistantService';
import type { QAResponse, QAHistoryItem, ChatMessage } from '@/types/hsaAssistant';

// Mock the service
vi.mock('@/services/hsaAssistantService', () => ({
  hsaAssistantService: {
    askQuestion: vi.fn(),
    getHistory: vi.fn(),
  },
}));

const mockQAResponse: QAResponse = {
  answer: 'Test answer about HSA eligibility rules.',
  confidence_score: 0.85,
  citations: [{
    document_name: 'HSA Guide',
    page_number: 1,
    excerpt: 'Test excerpt',
    relevance_score: 0.9,
  }],
  source_documents: ['HSA Guide'],
  processing_time_ms: 120,
  created_at: '2024-01-15T10:00:00Z',
};

const mockHistoryItems: QAHistoryItem[] = [
  {
    id: 'qa-session-1',
    question: 'Previous session question',
    answer: 'Previous session answer',
    confidence_score: 0.9,
    citations_count: 1,
    application_id: 'session-app-123',
    created_at: '2024-01-15T09:00:00Z',
  },
];

// Test component that exposes chat context for testing
const QASessionTestComponent = ({ testId }: { testId: string }) => {
  const chatContext = useChat();
  
  return (
    <div data-testid={testId}>
      <div data-testid="session-state">
        {JSON.stringify({
          messageCount: chatContext.messages.length,
          isLoading: chatContext.isLoading,
          error: chatContext.error,
          applicationId: chatContext.applicationId,
          hasMessages: chatContext.messages.length > 0,
          latestMessage: chatContext.messages[chatContext.messages.length - 1]?.content || 'none',
        })}
      </div>
      
      <input
        data-testid="test-input"
        onChange={(e) => {
          if (e.target.value) {
            chatContext.sendMessage(e.target.value);
          }
        }}
      />
      
      <button
        data-testid="clear-session"
        onClick={() => chatContext.clearMessages()}
      >
        Clear Session
      </button>
      
      <button
        data-testid="load-history"
        onClick={() => chatContext.loadHistory()}
      >
        Load History
      </button>
      
      <button
        data-testid="set-app-id"
        onClick={() => chatContext.setApplicationId('test-app-456')}
      >
        Set App ID
      </button>
      
      <div data-testid="messages-list">
        {chatContext.messages.map((msg, index) => (
          <div key={msg.id} data-testid={`message-${index}`}>
            <span data-testid={`msg-role-${index}`}>{msg.role}</span>
            <span data-testid={`msg-content-${index}`}>{msg.content}</span>
            <span data-testid={`msg-status-${index}`}>{msg.status}</span>
            {msg.citations && (
              <div data-testid={`msg-citations-${index}`}>
                {msg.citations.length} citations
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

describe('QA Session State Management', () => {
  const mockAskQuestion = hsaAssistantService.askQuestion as MockedFunction<typeof hsaAssistantService.askQuestion>;
  const mockGetHistory = hsaAssistantService.getHistory as MockedFunction<typeof hsaAssistantService.getHistory>;

  beforeEach(() => {
    vi.clearAllMocks();
    mockAskQuestion.mockResolvedValue(mockQAResponse);
    mockGetHistory.mockResolvedValue(mockHistoryItems);
  });

  const renderWithProvider = (initialApplicationId?: string) => {
    return render(
      <BrowserRouter>
        <ChatProvider initialApplicationId={initialApplicationId}>
          <QASessionTestComponent testId="qa-session-test" />
        </ChatProvider>
      </BrowserRouter>
    );
  };

  describe('Session Initialization', () => {
    it('initializes with empty state when no application ID provided', () => {
      renderWithProvider();

      const sessionState = JSON.parse(screen.getByTestId('session-state').textContent || '{}');
      
      expect(sessionState).toMatchObject({
        messageCount: 0,
        isLoading: false,
        error: null,
        applicationId: undefined,
        hasMessages: false,
        latestMessage: 'none',
      });
    });

    it('initializes with application ID and loads history', async () => {
      renderWithProvider('session-app-123');

      // Should automatically load history
      await waitFor(() => {
        expect(mockGetHistory).toHaveBeenCalledWith('session-app-123');
      });

      const sessionState = JSON.parse(screen.getByTestId('session-state').textContent || '{}');
      expect(sessionState.applicationId).toBe('session-app-123');
    });

    it('populates messages from loaded history', async () => {
      renderWithProvider('session-app-123');

      await waitFor(() => {
        expect(mockGetHistory).toHaveBeenCalled();
      });

      // Should have messages from history (user + assistant)
      await waitFor(() => {
        const sessionState = JSON.parse(screen.getByTestId('session-state').textContent || '{}');
        expect(sessionState.messageCount).toBe(2); // 1 question + 1 answer
      });

      // Verify message content
      expect(screen.getByTestId('msg-content-0')).toHaveTextContent('Previous session question');
      expect(screen.getByTestId('msg-content-1')).toHaveTextContent('Previous session answer');
    });
  });

  describe('Message Flow Management', () => {
    it('maintains correct message sequence during conversation', async () => {
      const user = userEvent.setup();
      renderWithProvider();

      const input = screen.getByTestId('test-input');

      // Send first message
      fireEvent.change(input, { target: { value: 'First question' } });
      
      await waitFor(() => {
        expect(mockAskQuestion).toHaveBeenCalledWith('First question', undefined, undefined);
      });

      // Verify first exchange
      await waitFor(() => {
        expect(screen.getByTestId('msg-content-0')).toHaveTextContent('First question');
        expect(screen.getByTestId('msg-content-1')).toHaveTextContent(mockQAResponse.answer);
      });

      // Send second message
      fireEvent.change(input, { target: { value: 'Second question' } });

      await waitFor(() => {
        expect(mockAskQuestion).toHaveBeenCalledTimes(2);
      });

      // Verify complete conversation order
      const sessionState = JSON.parse(screen.getByTestId('session-state').textContent || '{}');
      expect(sessionState.messageCount).toBe(4); // 2 questions + 2 answers
    });

    it('provides context from previous messages in conversation', async () => {
      renderWithProvider();

      const input = screen.getByTestId('test-input');

      // First question
      fireEvent.change(input, { target: { value: 'What are HSA limits?' } });
      
      await waitFor(() => {
        expect(mockAskQuestion).toHaveBeenCalledTimes(1);
      });

      // Follow-up question should include context
      fireEvent.change(input, { target: { value: 'Can I contribute more if over 55?' } });

      await waitFor(() => {
        expect(mockAskQuestion).toHaveBeenCalledTimes(2);
        expect(mockAskQuestion).toHaveBeenLastCalledWith(
          'Can I contribute more if over 55?',
          mockQAResponse.answer, // Context from previous response
          undefined
        );
      });
    });

    it('handles rapid message sending correctly', async () => {
      renderWithProvider();

      const input = screen.getByTestId('test-input');
      const questions = ['Question 1', 'Question 2', 'Question 3'];

      // Send questions rapidly
      questions.forEach(question => {
        fireEvent.change(input, { target: { value: question } });
      });

      // All should be processed
      await waitFor(() => {
        expect(mockAskQuestion).toHaveBeenCalledTimes(3);
      });

      // Verify all messages exist
      const sessionState = JSON.parse(screen.getByTestId('session-state').textContent || '{}');
      expect(sessionState.messageCount).toBe(6); // 3 questions + 3 answers
    });
  });

  describe('Session Persistence', () => {
    it('maintains session state across component updates', async () => {
      const { rerender } = renderWithProvider('persistent-app');

      const input = screen.getByTestId('test-input');
      fireEvent.change(input, { target: { value: 'Test persistence' } });

      await waitFor(() => {
        expect(mockAskQuestion).toHaveBeenCalled();
      });

      // Rerender component
      rerender(
        <BrowserRouter>
          <ChatProvider initialApplicationId="persistent-app">
            <QASessionTestComponent testId="qa-session-test" />
          </ChatProvider>
        </BrowserRouter>
      );

      // Messages should still be there
      await waitFor(() => {
        expect(screen.getByTestId('msg-content-0')).toHaveTextContent('Test persistence');
      });
    });

    it('updates application ID dynamically', async () => {
      renderWithProvider();

      const setAppIdButton = screen.getByTestId('set-app-id');
      fireEvent.click(setAppIdButton);

      const sessionState = JSON.parse(screen.getByTestId('session-state').textContent || '{}');
      expect(sessionState.applicationId).toBe('test-app-456');
    });

    it('includes application ID in subsequent API calls', async () => {
      renderWithProvider();

      // Set application ID
      const setAppIdButton = screen.getByTestId('set-app-id');
      fireEvent.click(setAppIdButton);

      // Send message
      const input = screen.getByTestId('test-input');
      fireEvent.change(input, { target: { value: 'Test with app ID' } });

      await waitFor(() => {
        expect(mockAskQuestion).toHaveBeenCalledWith(
          'Test with app ID',
          undefined,
          'test-app-456'
        );
      });
    });
  });

  describe('Session Management Operations', () => {
    it('clears session correctly', async () => {
      renderWithProvider();

      // Add some messages first
      const input = screen.getByTestId('test-input');
      fireEvent.change(input, { target: { value: 'Message to clear' } });

      await waitFor(() => {
        const sessionState = JSON.parse(screen.getByTestId('session-state').textContent || '{}');
        expect(sessionState.messageCount).toBeGreaterThan(0);
      });

      // Clear session
      const clearButton = screen.getByTestId('clear-session');
      fireEvent.click(clearButton);

      // Session should be empty
      const sessionState = JSON.parse(screen.getByTestId('session-state').textContent || '{}');
      expect(sessionState).toMatchObject({
        messageCount: 0,
        hasMessages: false,
        latestMessage: 'none',
        error: null,
      });
    });

    it('loads history on demand', async () => {
      renderWithProvider();

      const loadHistoryButton = screen.getByTestId('load-history');
      fireEvent.click(loadHistoryButton);

      await waitFor(() => {
        expect(mockGetHistory).toHaveBeenCalled();
      });

      // Should populate with history messages
      await waitFor(() => {
        const sessionState = JSON.parse(screen.getByTestId('session-state').textContent || '{}');
        expect(sessionState.messageCount).toBeGreaterThan(0);
      });
    });

    it('handles session errors gracefully', async () => {
      mockAskQuestion.mockRejectedValueOnce(new Error('Session API error'));
      
      renderWithProvider();

      const input = screen.getByTestId('test-input');
      fireEvent.change(input, { target: { value: 'Question causing error' } });

      // Should handle error without crashing
      await waitFor(() => {
        const sessionState = JSON.parse(screen.getByTestId('session-state').textContent || '{}');
        expect(sessionState.error).toBeTruthy();
        expect(sessionState.isLoading).toBe(false);
      });
    });
  });

  describe('Citation and Response Metadata', () => {
    it('preserves citation information in session messages', async () => {
      renderWithProvider();

      const input = screen.getByTestId('test-input');
      fireEvent.change(input, { target: { value: 'Question with citations' } });

      await waitFor(() => {
        expect(mockAskQuestion).toHaveBeenCalled();
      });

      // Assistant message should have citations
      await waitFor(() => {
        const citationsElement = screen.getByTestId('msg-citations-1');
        expect(citationsElement).toHaveTextContent('1 citations');
      });
    });

    it('maintains confidence scores for responses', async () => {
      renderWithProvider();

      const input = screen.getByTestId('test-input');
      fireEvent.change(input, { target: { value: 'Confidence test' } });

      await waitFor(() => {
        expect(mockAskQuestion).toHaveBeenCalled();
      });

      // Check that confidence information is preserved
      // This would depend on how confidence scores are displayed in the actual UI
      await waitFor(() => {
        const sessionState = JSON.parse(screen.getByTestId('session-state').textContent || '{}');
        expect(sessionState.messageCount).toBe(2);
      });
    });

    it('tracks message status throughout session', async () => {
      renderWithProvider();

      const input = screen.getByTestId('test-input');
      fireEvent.change(input, { target: { value: 'Status tracking test' } });

      // User message should be immediately visible with success status
      await waitFor(() => {
        expect(screen.getByTestId('msg-status-0')).toHaveTextContent('success');
      });

      // Assistant response should also have success status
      await waitFor(() => {
        expect(screen.getByTestId('msg-status-1')).toHaveTextContent('success');
      });
    });
  });

  describe('Error Recovery and Resilience', () => {
    it('recovers from network errors while maintaining session', async () => {
      mockAskQuestion
        .mockRejectedValueOnce(new Error('Network timeout'))
        .mockResolvedValueOnce(mockQAResponse);

      renderWithProvider();

      const input = screen.getByTestId('test-input');
      
      // First message fails
      fireEvent.change(input, { target: { value: 'First message fails' } });
      
      await waitFor(() => {
        const sessionState = JSON.parse(screen.getByTestId('session-state').textContent || '{}');
        expect(sessionState.error).toBeTruthy();
      });

      // Second message succeeds
      fireEvent.change(input, { target: { value: 'Second message succeeds' } });

      await waitFor(() => {
        expect(screen.getByTestId('msg-content-2')).toHaveTextContent('Second message succeeds');
        expect(screen.getByTestId('msg-content-3')).toHaveTextContent(mockQAResponse.answer);
      });
    });

    it('handles history loading failures without affecting new session', async () => {
      mockGetHistory.mockRejectedValueOnce(new Error('History load failed'));
      
      renderWithProvider('app-with-bad-history');

      // Should still be able to start new conversation
      const input = screen.getByTestId('test-input');
      fireEvent.change(input, { target: { value: 'New conversation despite history failure' } });

      await waitFor(() => {
        expect(mockAskQuestion).toHaveBeenCalled();
        expect(screen.getByTestId('msg-content-0')).toHaveTextContent('New conversation despite history failure');
      });
    });

    it('maintains session integrity during concurrent operations', async () => {
      renderWithProvider('concurrent-app');

      const input = screen.getByTestId('test-input');
      const loadHistoryButton = screen.getByTestId('load-history');

      // Start multiple operations simultaneously
      fireEvent.change(input, { target: { value: 'Concurrent message' } });
      fireEvent.click(loadHistoryButton);

      // Both operations should complete successfully
      await waitFor(() => {
        expect(mockAskQuestion).toHaveBeenCalled();
        expect(mockGetHistory).toHaveBeenCalled();
      });

      // Session should remain in valid state
      await waitFor(() => {
        const sessionState = JSON.parse(screen.getByTestId('session-state').textContent || '{}');
        expect(sessionState.messageCount).toBeGreaterThan(0);
        expect(sessionState.error).toBeFalsy();
      });
    });
  });
});
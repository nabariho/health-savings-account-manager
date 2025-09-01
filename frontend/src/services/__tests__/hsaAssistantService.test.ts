/**
 * Tests for HSAAssistantService.
 * 
 * Tests API communication for HSA Assistant including question asking,
 * history retrieval, example questions, health checks, error handling,
 * and proper request/response formatting.
 */

import { vi, type MockedFunction } from 'vitest';
import { HSAAssistantService, hsaAssistantService } from '../hsaAssistantService';
import apiClient, { handleApiError } from '../api';
import type { QARequest, QAResponse, QAHistoryItem } from '@/types/hsaAssistant';

// Mock the API client and error handler
vi.mock('../api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
  handleApiError: vi.fn(),
}));

const mockApiClient = apiClient as {
  post: MockedFunction<any>;
  get: MockedFunction<any>;
};
const mockHandleApiError = handleApiError as MockedFunction<typeof handleApiError>;

describe('HSAAssistantService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('askQuestion', () => {
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

    it('sends question with minimal parameters', async () => {
      mockApiClient.post.mockResolvedValueOnce({ data: mockQAResponse });

      const result = await hsaAssistantService.askQuestion('What are HSA contribution limits?');

      expect(mockApiClient.post).toHaveBeenCalledWith('/hsa_assistant/ask', {
        question: 'What are HSA contribution limits?',
        context: undefined,
        application_id: undefined,
      });
      expect(result).toEqual(mockQAResponse);
    });

    it('sends question with all parameters', async () => {
      mockApiClient.post.mockResolvedValueOnce({ data: mockQAResponse });

      const result = await hsaAssistantService.askQuestion(
        'Can I contribute more?',
        'Previous context about HSA limits',
        'app-123'
      );

      expect(mockApiClient.post).toHaveBeenCalledWith('/hsa_assistant/ask', {
        question: 'Can I contribute more?',
        context: 'Previous context about HSA limits',
        application_id: 'app-123',
      });
      expect(result).toEqual(mockQAResponse);
    });

    it('handles API errors correctly', async () => {
      const apiError = new Error('Network error');
      const handledError = new Error('Handled network error');
      
      mockApiClient.post.mockRejectedValueOnce(apiError);
      mockHandleApiError.mockReturnValueOnce(handledError);

      await expect(hsaAssistantService.askQuestion('Test question')).rejects.toThrow('Handled network error');

      expect(mockHandleApiError).toHaveBeenCalledWith(apiError);
    });

    it('validates request format', async () => {
      mockApiClient.post.mockResolvedValueOnce({ data: mockQAResponse });

      await hsaAssistantService.askQuestion('Test question', 'context', 'app-id');

      const expectedRequest: QARequest = {
        question: 'Test question',
        context: 'context',
        application_id: 'app-id',
      };

      expect(mockApiClient.post).toHaveBeenCalledWith('/hsa_assistant/ask', expectedRequest);
    });

    it('handles empty question', async () => {
      mockApiClient.post.mockResolvedValueOnce({ data: mockQAResponse });

      await hsaAssistantService.askQuestion('');

      expect(mockApiClient.post).toHaveBeenCalledWith('/hsa_assistant/ask', {
        question: '',
        context: undefined,
        application_id: undefined,
      });
    });

    it('handles long question', async () => {
      const longQuestion = 'A'.repeat(1000);
      mockApiClient.post.mockResolvedValueOnce({ data: mockQAResponse });

      await hsaAssistantService.askQuestion(longQuestion);

      expect(mockApiClient.post).toHaveBeenCalledWith('/hsa_assistant/ask', {
        question: longQuestion,
        context: undefined,
        application_id: undefined,
      });
    });
  });

  describe('getHistory', () => {
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
        question: 'Can I use HSA for dental?',
        answer: 'Yes, dental expenses are qualified HSA expenses.',
        confidence_score: 0.88,
        citations_count: 2,
        created_at: '2024-01-15T10:05:00Z',
      },
    ];

    it('gets history with default parameters', async () => {
      mockApiClient.get.mockResolvedValueOnce({ data: mockHistoryItems });

      const result = await hsaAssistantService.getHistory();

      expect(mockApiClient.get).toHaveBeenCalledWith('/hsa_assistant/history/all', {
        params: { limit: 50, offset: 0 },
      });
      expect(result).toEqual(mockHistoryItems);
    });

    it('gets history with specific application ID', async () => {
      mockApiClient.get.mockResolvedValueOnce({ data: mockHistoryItems });

      const result = await hsaAssistantService.getHistory('app-456');

      expect(mockApiClient.get).toHaveBeenCalledWith('/hsa_assistant/history/app-456', {
        params: { limit: 50, offset: 0 },
      });
      expect(result).toEqual(mockHistoryItems);
    });

    it('gets history with custom limit and offset', async () => {
      mockApiClient.get.mockResolvedValueOnce({ data: mockHistoryItems });

      const result = await hsaAssistantService.getHistory('all', 25, 10);

      expect(mockApiClient.get).toHaveBeenCalledWith('/hsa_assistant/history/all', {
        params: { limit: 25, offset: 10 },
      });
      expect(result).toEqual(mockHistoryItems);
    });

    it('handles empty history response', async () => {
      mockApiClient.get.mockResolvedValueOnce({ data: [] });

      const result = await hsaAssistantService.getHistory();

      expect(result).toEqual([]);
    });

    it('handles API errors correctly', async () => {
      const apiError = new Error('Unauthorized access');
      const handledError = new Error('Handled auth error');
      
      mockApiClient.get.mockRejectedValueOnce(apiError);
      mockHandleApiError.mockReturnValueOnce(handledError);

      await expect(hsaAssistantService.getHistory()).rejects.toThrow('Handled auth error');

      expect(mockHandleApiError).toHaveBeenCalledWith(apiError);
    });

    it('handles zero limit', async () => {
      mockApiClient.get.mockResolvedValueOnce({ data: [] });

      await hsaAssistantService.getHistory('all', 0);

      expect(mockApiClient.get).toHaveBeenCalledWith('/hsa_assistant/history/all', {
        params: { limit: 0, offset: 0 },
      });
    });

    it('handles large offset', async () => {
      mockApiClient.get.mockResolvedValueOnce({ data: [] });

      await hsaAssistantService.getHistory('all', 50, 10000);

      expect(mockApiClient.get).toHaveBeenCalledWith('/hsa_assistant/history/all', {
        params: { limit: 50, offset: 10000 },
      });
    });
  });

  describe('getExampleQuestions', () => {
    const mockExamples = {
      example_questions: [
        'What are the HSA contribution limits for 2024?',
        'Am I eligible for an HSA?',
        'Can I use my HSA for dental expenses?',
      ],
    };

    it('gets example questions successfully', async () => {
      mockApiClient.get.mockResolvedValueOnce({ data: mockExamples });

      const result = await hsaAssistantService.getExampleQuestions();

      expect(mockApiClient.get).toHaveBeenCalledWith('/hsa_assistant/examples');
      expect(result).toEqual(mockExamples.example_questions);
    });

    it('handles empty examples response', async () => {
      mockApiClient.get.mockResolvedValueOnce({ data: { example_questions: [] } });

      const result = await hsaAssistantService.getExampleQuestions();

      expect(result).toEqual([]);
    });

    it('handles API errors correctly', async () => {
      const apiError = new Error('Service unavailable');
      const handledError = new Error('Handled service error');
      
      mockApiClient.get.mockRejectedValueOnce(apiError);
      mockHandleApiError.mockReturnValueOnce(handledError);

      await expect(hsaAssistantService.getExampleQuestions()).rejects.toThrow('Handled service error');

      expect(mockHandleApiError).toHaveBeenCalledWith(apiError);
    });
  });

  describe('healthCheck', () => {
    const mockHealthResponse = {
      status: 'healthy',
      service: 'HSA Assistant',
    };

    it('performs health check successfully', async () => {
      mockApiClient.get.mockResolvedValueOnce({ data: mockHealthResponse });

      const result = await hsaAssistantService.healthCheck();

      expect(mockApiClient.get).toHaveBeenCalledWith('/hsa_assistant/health');
      expect(result).toEqual(mockHealthResponse);
    });

    it('handles unhealthy service response', async () => {
      const unhealthyResponse = {
        status: 'unhealthy',
        service: 'HSA Assistant',
      };
      
      mockApiClient.get.mockResolvedValueOnce({ data: unhealthyResponse });

      const result = await hsaAssistantService.healthCheck();

      expect(result).toEqual(unhealthyResponse);
    });

    it('handles API errors correctly', async () => {
      const apiError = new Error('Connection timeout');
      const handledError = new Error('Handled connection error');
      
      mockApiClient.get.mockRejectedValueOnce(apiError);
      mockHandleApiError.mockReturnValueOnce(handledError);

      await expect(hsaAssistantService.healthCheck()).rejects.toThrow('Handled connection error');

      expect(mockHandleApiError).toHaveBeenCalledWith(apiError);
    });
  });

  describe('Service Instance', () => {
    it('exports singleton instance', () => {
      expect(hsaAssistantService).toBeInstanceOf(HSAAssistantService);
    });

    it('uses correct base path', () => {
      const service = new HSAAssistantService();
      // We can't directly test private properties, but we can test the API calls use the right path
      mockApiClient.post.mockResolvedValueOnce({ data: {} });
      
      service.askQuestion('test');
      
      expect(mockApiClient.post).toHaveBeenCalledWith('/hsa_assistant/ask', expect.any(Object));
    });
  });

  describe('Error Handling', () => {
    it('propagates handleApiError results for askQuestion', async () => {
      const originalError = { response: { status: 400, data: { error: 'Bad Request' } } };
      const handledError = new Error('Validation failed');
      
      mockApiClient.post.mockRejectedValueOnce(originalError);
      mockHandleApiError.mockReturnValueOnce(handledError);

      await expect(hsaAssistantService.askQuestion('test')).rejects.toThrow('Validation failed');
      expect(mockHandleApiError).toHaveBeenCalledWith(originalError);
    });

    it('propagates handleApiError results for getHistory', async () => {
      const originalError = { response: { status: 404, data: { error: 'Not Found' } } };
      const handledError = new Error('History not found');
      
      mockApiClient.get.mockRejectedValueOnce(originalError);
      mockHandleApiError.mockReturnValueOnce(handledError);

      await expect(hsaAssistantService.getHistory()).rejects.toThrow('History not found');
      expect(mockHandleApiError).toHaveBeenCalledWith(originalError);
    });

    it('propagates handleApiError results for getExampleQuestions', async () => {
      const originalError = { response: { status: 500, data: { error: 'Internal Server Error' } } };
      const handledError = new Error('Server error occurred');
      
      mockApiClient.get.mockRejectedValueOnce(originalError);
      mockHandleApiError.mockReturnValueOnce(handledError);

      await expect(hsaAssistantService.getExampleQuestions()).rejects.toThrow('Server error occurred');
      expect(mockHandleApiError).toHaveBeenCalledWith(originalError);
    });

    it('propagates handleApiError results for healthCheck', async () => {
      const originalError = { response: { status: 503, data: { error: 'Service Unavailable' } } };
      const handledError = new Error('Service temporarily unavailable');
      
      mockApiClient.get.mockRejectedValueOnce(originalError);
      mockHandleApiError.mockReturnValueOnce(handledError);

      await expect(hsaAssistantService.healthCheck()).rejects.toThrow('Service temporarily unavailable');
      expect(mockHandleApiError).toHaveBeenCalledWith(originalError);
    });
  });

  describe('Response Data Extraction', () => {
    it('correctly extracts data from askQuestion response', async () => {
      const responseData = { answer: 'Test answer', confidence_score: 0.9, citations: [], source_documents: [], created_at: '2024-01-01T00:00:00Z' };
      mockApiClient.post.mockResolvedValueOnce({ data: responseData, status: 200, statusText: 'OK' });

      const result = await hsaAssistantService.askQuestion('test');

      expect(result).toEqual(responseData);
    });

    it('correctly extracts data from getHistory response', async () => {
      const responseData = [{ id: '1', question: 'test', answer: 'test answer', confidence_score: 0.9, citations_count: 0, created_at: '2024-01-01T00:00:00Z' }];
      mockApiClient.get.mockResolvedValueOnce({ data: responseData, status: 200, statusText: 'OK' });

      const result = await hsaAssistantService.getHistory();

      expect(result).toEqual(responseData);
    });

    it('correctly extracts data from getExampleQuestions response', async () => {
      const responseData = { example_questions: ['question 1', 'question 2'] };
      mockApiClient.get.mockResolvedValueOnce({ data: responseData, status: 200, statusText: 'OK' });

      const result = await hsaAssistantService.getExampleQuestions();

      expect(result).toEqual(responseData.example_questions);
    });

    it('correctly extracts data from healthCheck response', async () => {
      const responseData = { status: 'healthy', service: 'HSA Assistant' };
      mockApiClient.get.mockResolvedValueOnce({ data: responseData, status: 200, statusText: 'OK' });

      const result = await hsaAssistantService.healthCheck();

      expect(result).toEqual(responseData);
    });
  });

  describe('Special Characters and Edge Cases', () => {
    it('handles questions with special characters', async () => {
      const specialQuestion = 'What about HSA for $10,000+ expenses? <>&"\'';
      mockApiClient.post.mockResolvedValueOnce({ data: { answer: 'Response', confidence_score: 0.8, citations: [], source_documents: [], created_at: '2024-01-01T00:00:00Z' } });

      await hsaAssistantService.askQuestion(specialQuestion);

      expect(mockApiClient.post).toHaveBeenCalledWith('/hsa_assistant/ask', {
        question: specialQuestion,
        context: undefined,
        application_id: undefined,
      });
    });

    it('handles Unicode characters in questions', async () => {
      const unicodeQuestion = 'HSA für deutsche Bürger? 中文 🏥💰';
      mockApiClient.post.mockResolvedValueOnce({ data: { answer: 'Response', confidence_score: 0.8, citations: [], source_documents: [], created_at: '2024-01-01T00:00:00Z' } });

      await hsaAssistantService.askQuestion(unicodeQuestion);

      expect(mockApiClient.post).toHaveBeenCalledWith('/hsa_assistant/ask', {
        question: unicodeQuestion,
        context: undefined,
        application_id: undefined,
      });
    });

    it('handles special application IDs', async () => {
      const specialAppId = 'app-123_test.2024@example.com';
      mockApiClient.get.mockResolvedValueOnce({ data: [] });

      await hsaAssistantService.getHistory(specialAppId);

      expect(mockApiClient.get).toHaveBeenCalledWith(`/hsa_assistant/history/${specialAppId}`, {
        params: { limit: 50, offset: 0 },
      });
    });
  });
});
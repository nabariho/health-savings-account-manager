/**
 * API Integration Tests for HSA Assistant.
 * 
 * Tests API integration with mocked backend responses including success scenarios,
 * error handling, network issues, rate limiting, authentication, and edge cases.
 */

import { vi, type MockedFunction } from 'vitest';
import axios from 'axios';
import { hsaAssistantService } from '../hsaAssistantService';
import { handleApiError } from '../api';
import type { QAResponse, QAHistoryItem } from '@/types/hsaAssistant';

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      post: vi.fn(),
      get: vi.fn(),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    })),
  },
}));

// Create mock axios instance
const mockAxios = {
  post: vi.fn(),
  get: vi.fn(),
  interceptors: {
    request: { use: vi.fn() },
    response: { use: vi.fn() },
  },
};

(axios.create as MockedFunction<typeof axios.create>).mockReturnValue(mockAxios as any);

describe('API Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('HSA Assistant API Success Scenarios', () => {
    it('successfully asks question and receives response with citations', async () => {
      const mockResponse: QAResponse = {
        answer: 'The HSA contribution limit for 2024 is $4,150 for individual coverage.',
        confidence_score: 0.92,
        citations: [
          {
            document_name: 'IRS Publication 969',
            page_number: 3,
            excerpt: 'For 2024, the annual contribution limit is $4,150.',
            relevance_score: 0.95,
          },
          {
            document_name: 'HSA Guidelines 2024',
            excerpt: 'Individual coverage limit set at $4,150 for tax year 2024.',
            relevance_score: 0.88,
          },
        ],
        source_documents: ['IRS Publication 969', 'HSA Guidelines 2024'],
        processing_time_ms: 145,
        created_at: '2024-01-15T10:00:05Z',
      };

      mockAxios.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await hsaAssistantService.askQuestion(
        'What are the HSA contribution limits for 2024?'
      );

      expect(result).toEqual(mockResponse);
      expect(mockAxios.post).toHaveBeenCalledWith('/hsa_assistant/ask', {
        question: 'What are the HSA contribution limits for 2024?',
        context: undefined,
        application_id: undefined,
      });
    });

    it('successfully retrieves chat history with pagination', async () => {
      const mockHistory: QAHistoryItem[] = [
        {
          id: 'qa-1',
          question: 'What are HSA contribution limits?',
          answer: 'The HSA contribution limit for 2024 is $4,150.',
          confidence_score: 0.92,
          citations_count: 2,
          application_id: 'app-123',
          created_at: '2024-01-15T10:00:00Z',
        },
        {
          id: 'qa-2',
          question: 'Can I use HSA for dental expenses?',
          answer: 'Yes, dental expenses are qualified HSA expenses.',
          confidence_score: 0.88,
          citations_count: 1,
          application_id: 'app-123',
          created_at: '2024-01-15T10:05:00Z',
        },
      ];

      mockAxios.get.mockResolvedValueOnce({ data: mockHistory });

      const result = await hsaAssistantService.getHistory('app-123', 10, 0);

      expect(result).toEqual(mockHistory);
      expect(mockAxios.get).toHaveBeenCalledWith('/hsa_assistant/history/app-123', {
        params: { limit: 10, offset: 0 },
      });
    });

    it('successfully retrieves example questions', async () => {
      const mockExamples = {
        example_questions: [
          'What are the HSA contribution limits for 2024?',
          'Am I eligible for an HSA if I have other health insurance?',
          'Can I use my HSA for dental expenses?',
          'What happens to my HSA when I turn 65?',
          'How do I withdraw money from my HSA?',
        ],
      };

      mockAxios.get.mockResolvedValueOnce({ data: mockExamples });

      const result = await hsaAssistantService.getExampleQuestions();

      expect(result).toEqual(mockExamples.example_questions);
      expect(mockAxios.get).toHaveBeenCalledWith('/hsa_assistant/examples');
    });

    it('successfully performs health check', async () => {
      const mockHealthResponse = {
        status: 'healthy',
        service: 'HSA Assistant',
      };

      mockAxios.get.mockResolvedValueOnce({ data: mockHealthResponse });

      const result = await hsaAssistantService.healthCheck();

      expect(result).toEqual(mockHealthResponse);
      expect(mockAxios.get).toHaveBeenCalledWith('/hsa_assistant/health');
    });
  });

  describe('Error Handling Scenarios', () => {
    it('handles 400 Bad Request errors', async () => {
      const errorResponse = {
        response: {
          status: 400,
          data: {
            error: 'Invalid question format',
            details: 'Question cannot be empty',
          },
        },
      };

      mockAxios.post.mockRejectedValueOnce(errorResponse);

      await expect(hsaAssistantService.askQuestion('')).rejects.toThrow();
    });

    it('handles 401 Unauthorized errors', async () => {
      const errorResponse = {
        response: {
          status: 401,
          data: {
            error: 'Unauthorized',
            message: 'Invalid or missing authentication token',
          },
        },
      };

      mockAxios.get.mockRejectedValueOnce(errorResponse);

      await expect(hsaAssistantService.getHistory()).rejects.toThrow();
    });

    it('handles 403 Forbidden errors', async () => {
      const errorResponse = {
        response: {
          status: 403,
          data: {
            error: 'Forbidden',
            message: 'Insufficient permissions to access this resource',
          },
        },
      };

      mockAxios.get.mockRejectedValueOnce(errorResponse);

      await expect(hsaAssistantService.getHistory('restricted-app')).rejects.toThrow();
    });

    it('handles 404 Not Found errors', async () => {
      const errorResponse = {
        response: {
          status: 404,
          data: {
            error: 'Not Found',
            message: 'Application history not found',
          },
        },
      };

      mockAxios.get.mockRejectedValueOnce(errorResponse);

      await expect(hsaAssistantService.getHistory('nonexistent-app')).rejects.toThrow();
    });

    it('handles 429 Rate Limit errors', async () => {
      const errorResponse = {
        response: {
          status: 429,
          data: {
            error: 'Rate limit exceeded',
            message: 'Too many requests. Please try again later.',
            retry_after: 60,
          },
        },
      };

      mockAxios.post.mockRejectedValueOnce(errorResponse);

      await expect(hsaAssistantService.askQuestion('Test question')).rejects.toThrow();
    });

    it('handles 500 Internal Server Error', async () => {
      const errorResponse = {
        response: {
          status: 500,
          data: {
            error: 'Internal Server Error',
            message: 'An unexpected error occurred',
          },
        },
      };

      mockAxios.post.mockRejectedValueOnce(errorResponse);

      await expect(hsaAssistantService.askQuestion('Test question')).rejects.toThrow();
    });

    it('handles 502 Bad Gateway errors', async () => {
      const errorResponse = {
        response: {
          status: 502,
          data: {
            error: 'Bad Gateway',
            message: 'HSA Assistant service is temporarily unavailable',
          },
        },
      };

      mockAxios.get.mockRejectedValueOnce(errorResponse);

      await expect(hsaAssistantService.healthCheck()).rejects.toThrow();
    });

    it('handles 503 Service Unavailable errors', async () => {
      const errorResponse = {
        response: {
          status: 503,
          data: {
            error: 'Service Unavailable',
            message: 'HSA Assistant is under maintenance',
          },
        },
      };

      mockAxios.post.mockRejectedValueOnce(errorResponse);

      await expect(hsaAssistantService.askQuestion('Test question')).rejects.toThrow();
    });

    it('handles network timeout errors', async () => {
      const networkError = new Error('Network Error');
      networkError.name = 'ETIMEDOUT';

      mockAxios.post.mockRejectedValueOnce(networkError);

      await expect(hsaAssistantService.askQuestion('Test question')).rejects.toThrow();
    });

    it('handles connection refused errors', async () => {
      const connectionError = new Error('Network Error');
      connectionError.name = 'ECONNREFUSED';

      mockAxios.get.mockRejectedValueOnce(connectionError);

      await expect(hsaAssistantService.healthCheck()).rejects.toThrow();
    });
  });

  describe('Edge Cases and Data Validation', () => {
    it('handles response with missing citations', async () => {
      const responseWithoutCitations: QAResponse = {
        answer: 'HSAs are tax-advantaged accounts.',
        confidence_score: 0.75,
        citations: [],
        source_documents: [],
        created_at: '2024-01-15T10:00:05Z',
      };

      mockAxios.post.mockResolvedValueOnce({ data: responseWithoutCitations });

      const result = await hsaAssistantService.askQuestion('What is an HSA?');

      expect(result.citations).toEqual([]);
      expect(result.source_documents).toEqual([]);
    });

    it('handles response with low confidence score', async () => {
      const lowConfidenceResponse: QAResponse = {
        answer: 'I am not certain about this specific requirement.',
        confidence_score: 0.35,
        citations: [],
        source_documents: [],
        created_at: '2024-01-15T10:00:05Z',
      };

      mockAxios.post.mockResolvedValueOnce({ data: lowConfidenceResponse });

      const result = await hsaAssistantService.askQuestion('Very specific edge case question');

      expect(result.confidence_score).toBe(0.35);
    });

    it('handles empty history response', async () => {
      mockAxios.get.mockResolvedValueOnce({ data: [] });

      const result = await hsaAssistantService.getHistory('new-app');

      expect(result).toEqual([]);
    });

    it('handles very long question text', async () => {
      const longQuestion = 'A'.repeat(2000); // 2000 character question
      const mockResponse: QAResponse = {
        answer: 'I understand you have a detailed question about HSA.',
        confidence_score: 0.8,
        citations: [],
        source_documents: [],
        created_at: '2024-01-15T10:00:05Z',
      };

      mockAxios.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await hsaAssistantService.askQuestion(longQuestion);

      expect(result).toEqual(mockResponse);
      expect(mockAxios.post).toHaveBeenCalledWith('/hsa_assistant/ask', {
        question: longQuestion,
        context: undefined,
        application_id: undefined,
      });
    });

    it('handles questions with special characters and encoding', async () => {
      const specialQuestion = 'HSA für deutsche Bürger? Cost: $10,000+ & <coverage> "quotes" 中文';
      const mockResponse: QAResponse = {
        answer: 'HSA rules apply to US residents with qualifying health plans.',
        confidence_score: 0.85,
        citations: [],
        source_documents: [],
        created_at: '2024-01-15T10:00:05Z',
      };

      mockAxios.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await hsaAssistantService.askQuestion(specialQuestion);

      expect(result).toEqual(mockResponse);
    });

    it('handles large history datasets with pagination', async () => {
      const largeHistoryBatch = Array.from({ length: 100 }, (_, i) => ({
        id: `qa-${i + 1}`,
        question: `Question ${i + 1}`,
        answer: `Answer ${i + 1}`,
        confidence_score: 0.8 + (i % 20) * 0.01,
        citations_count: i % 3,
        application_id: 'large-app',
        created_at: `2024-01-15T${(10 + i % 14).toString().padStart(2, '0')}:00:00Z`,
      }));

      mockAxios.get.mockResolvedValueOnce({ data: largeHistoryBatch });

      const result = await hsaAssistantService.getHistory('large-app', 100, 0);

      expect(result).toHaveLength(100);
      expect(result[0].id).toBe('qa-1');
      expect(result[99].id).toBe('qa-100');
    });
  });

  describe('Performance and Timing Tests', () => {
    it('handles slow API responses', async () => {
      const slowResponse: QAResponse = {
        answer: 'This response took longer to process.',
        confidence_score: 0.9,
        citations: [],
        source_documents: [],
        processing_time_ms: 5000, // 5 second processing time
        created_at: '2024-01-15T10:00:05Z',
      };

      // Simulate slow response
      mockAxios.post.mockImplementationOnce(
        () => new Promise(resolve => 
          setTimeout(() => resolve({ data: slowResponse }), 100)
        )
      );

      const start = Date.now();
      const result = await hsaAssistantService.askQuestion('Complex question');
      const duration = Date.now() - start;

      expect(result).toEqual(slowResponse);
      expect(duration).toBeGreaterThanOrEqual(100);
    });

    it('includes processing time in responses', async () => {
      const timedResponse: QAResponse = {
        answer: 'Response with timing information.',
        confidence_score: 0.88,
        citations: [],
        source_documents: [],
        processing_time_ms: 234,
        created_at: '2024-01-15T10:00:05Z',
      };

      mockAxios.post.mockResolvedValueOnce({ data: timedResponse });

      const result = await hsaAssistantService.askQuestion('Timed question');

      expect(result.processing_time_ms).toBe(234);
    });
  });

  describe('Context and Follow-up Questions', () => {
    it('sends context with follow-up questions', async () => {
      const contextResponse: QAResponse = {
        answer: 'Based on the previous discussion about contribution limits, catch-up contributions are available.',
        confidence_score: 0.91,
        citations: [],
        source_documents: [],
        created_at: '2024-01-15T10:00:05Z',
      };

      mockAxios.post.mockResolvedValueOnce({ data: contextResponse });

      const result = await hsaAssistantService.askQuestion(
        'What about catch-up contributions?',
        'Previous conversation about HSA contribution limits of $4,150.',
        'app-123'
      );

      expect(result).toEqual(contextResponse);
      expect(mockAxios.post).toHaveBeenCalledWith('/hsa_assistant/ask', {
        question: 'What about catch-up contributions?',
        context: 'Previous conversation about HSA contribution limits of $4,150.',
        application_id: 'app-123',
      });
    });
  });

  describe('Application ID Tracking', () => {
    it('includes application ID in all relevant requests', async () => {
      const appId = 'tracking-app-456';
      
      // Test askQuestion with app ID
      const mockQAResponse: QAResponse = {
        answer: 'Tracked response',
        confidence_score: 0.9,
        citations: [],
        source_documents: [],
        created_at: '2024-01-15T10:00:05Z',
      };

      mockAxios.post.mockResolvedValueOnce({ data: mockQAResponse });
      mockAxios.get.mockResolvedValueOnce({ data: [] });

      await hsaAssistantService.askQuestion('Question with tracking', undefined, appId);
      await hsaAssistantService.getHistory(appId);

      expect(mockAxios.post).toHaveBeenCalledWith('/hsa_assistant/ask', {
        question: 'Question with tracking',
        context: undefined,
        application_id: appId,
      });

      expect(mockAxios.get).toHaveBeenCalledWith(`/hsa_assistant/history/${appId}`, {
        params: { limit: 50, offset: 0 },
      });
    });
  });

  describe('Citation Data Integrity', () => {
    it('preserves citation data structure and content', async () => {
      const responseWithRichCitations: QAResponse = {
        answer: 'Detailed answer with multiple sources.',
        confidence_score: 0.94,
        citations: [
          {
            document_name: 'IRS Publication 969 (2024)',
            page_number: 15,
            excerpt: 'Detailed excerpt with specific information about HSA eligibility requirements.',
            relevance_score: 0.97,
          },
          {
            document_name: 'Treasury Regulation 54.213-2',
            excerpt: 'Regulatory text defining high-deductible health plans.',
            relevance_score: 0.89,
          },
        ],
        source_documents: ['IRS Publication 969 (2024)', 'Treasury Regulation 54.213-2'],
        processing_time_ms: 180,
        created_at: '2024-01-15T10:00:05Z',
      };

      mockAxios.post.mockResolvedValueOnce({ data: responseWithRichCitations });

      const result = await hsaAssistantService.askQuestion('Complex eligibility question');

      expect(result.citations).toHaveLength(2);
      expect(result.citations[0]).toHaveProperty('document_name');
      expect(result.citations[0]).toHaveProperty('page_number');
      expect(result.citations[0]).toHaveProperty('excerpt');
      expect(result.citations[0]).toHaveProperty('relevance_score');
      expect(result.citations[1]).not.toHaveProperty('page_number'); // Optional field
    });
  });
});
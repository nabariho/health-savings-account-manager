/**
 * HSA Assistant service for handling chat API communication.
 * 
 * Provides methods for asking questions, retrieving chat history,
 * and interacting with the HSA Assistant backend service.
 */

import apiClient, { handleApiError } from './api';
import type {
  QARequest,
  QAResponse,
  QAHistoryItem,
} from '@/types/hsaAssistant';

/**
 * HSA Assistant service class for managing chat interactions.
 */
export class HSAAssistantService {
  private readonly basePath = '/hsa_assistant';

  /**
   * Ask a question to the HSA Assistant.
   * 
   * @param question - The question to ask
   * @param context - Optional context for follow-up questions
   * @param applicationId - Optional application ID for tracking
   * @returns Promise resolving to the QA response
   */
  async askQuestion(
    question: string,
    context?: string,
    applicationId?: string
  ): Promise<QAResponse> {
    try {
      const request: QARequest = {
        question,
        context,
        application_id: applicationId,
      };

      const response = await apiClient.post<QAResponse>(
        `${this.basePath}/ask`,
        request
      );

      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  /**
   * Get HSA Assistant chat history for an application.
   * 
   * @param applicationId - Application ID to get history for (use 'all' for all history)
   * @param limit - Maximum number of items to return
   * @param offset - Number of items to skip
   * @returns Promise resolving to the chat history
   */
  async getHistory(
    applicationId: string = 'all',
    limit: number = 50,
    offset: number = 0
  ): Promise<QAHistoryItem[]> {
    try {
      const response = await apiClient.get<QAHistoryItem[]>(
        `${this.basePath}/history/${applicationId}`,
        {
          params: { limit, offset },
        }
      );

      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  /**
   * Get example questions for testing and onboarding.
   * 
   * @returns Promise resolving to example questions
   */
  async getExampleQuestions(): Promise<string[]> {
    try {
      const response = await apiClient.get<{ example_questions: string[] }>(
        `${this.basePath}/examples`
      );

      return response.data.example_questions;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  /**
   * Check the health status of the HSA Assistant service.
   * 
   * @returns Promise resolving to health status
   */
  async healthCheck(): Promise<{ status: string; service: string }> {
    try {
      const response = await apiClient.get<{ status: string; service: string }>(
        `${this.basePath}/health`
      );

      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }
}

/**
 * Singleton instance of the HSA Assistant service.
 */
export const hsaAssistantService = new HSAAssistantService();

/**
 * Default export for convenience.
 */
export default hsaAssistantService;
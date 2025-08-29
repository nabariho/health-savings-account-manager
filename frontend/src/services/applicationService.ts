/**
 * Application service for managing HSA application data.
 * 
 * Provides methods for creating, retrieving, updating, and deleting
 * HSA applications through the backend API.
 */

import apiClient, { handleApiError } from './api';
import type {
  PersonalInfoRequest,
  ApplicationResponse,
  ApplicationUpdateRequest,
} from '@/types';

/**
 * Application service class with methods for all application operations.
 */
class ApplicationService {
  /**
   * Create a new HSA application with personal information.
   * 
   * @param personalInfo - Personal information data
   * @returns Promise<ApplicationResponse> - Created application data
   * @throws ApiError - If creation fails
   */
  async createApplication(personalInfo: PersonalInfoRequest): Promise<ApplicationResponse> {
    try {
      const response = await apiClient.post<ApplicationResponse>('/applications/', personalInfo);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  /**
   * Retrieve an application by ID.
   * 
   * @param applicationId - Application unique identifier
   * @returns Promise<ApplicationResponse> - Application data
   * @throws ApiError - If retrieval fails
   */
  async getApplication(applicationId: string): Promise<ApplicationResponse> {
    try {
      const response = await apiClient.get<ApplicationResponse>(`/applications/${applicationId}`);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  /**
   * Update an existing application.
   * 
   * @param applicationId - Application unique identifier
   * @param updateData - Fields to update
   * @returns Promise<ApplicationResponse> - Updated application data
   * @throws ApiError - If update fails
   */
  async updateApplication(
    applicationId: string,
    updateData: ApplicationUpdateRequest
  ): Promise<ApplicationResponse> {
    try {
      const response = await apiClient.put<ApplicationResponse>(
        `/applications/${applicationId}`,
        updateData
      );
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  /**
   * List applications with optional filtering.
   * 
   * @param params - Query parameters
   * @param params.status - Optional status filter
   * @param params.limit - Maximum number of applications to return
   * @param params.offset - Number of applications to skip
   * @returns Promise<ApplicationResponse[]> - List of applications
   * @throws ApiError - If listing fails
   */
  async listApplications(params: {
    status?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<ApplicationResponse[]> {
    try {
      const response = await apiClient.get<ApplicationResponse[]>('/applications/', {
        params,
      });
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }

  /**
   * Delete an application.
   * 
   * Only applications in pending status can be deleted.
   * 
   * @param applicationId - Application unique identifier
   * @throws ApiError - If deletion fails
   */
  async deleteApplication(applicationId: string): Promise<void> {
    try {
      await apiClient.delete(`/applications/${applicationId}`);
    } catch (error) {
      throw handleApiError(error);
    }
  }
}

// Export singleton instance
export const applicationService = new ApplicationService();
export default applicationService;
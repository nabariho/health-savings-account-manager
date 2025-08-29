/**
 * Document service for API interactions.
 * 
 * Handles all document-related API calls including upload, processing status,
 * and validation operations.
 */

import { apiClient } from './api';
import type {
  DocumentType,
  DocumentProcessingResponse,
  DocumentStatusResponse,
  DocumentValidationResponse,
} from '../types';

/**
 * Document service class for handling document operations.
 */
export class DocumentService {
  /**
   * Upload and process a document for an application.
   * 
   * @param applicationId - Application ID this document belongs to
   * @param documentType - Type of document being uploaded
   * @param file - File to upload
   * @returns Promise resolving to document processing response
   */
  static async uploadDocument(
    applicationId: string,
    documentType: DocumentType,
    file: File
  ): Promise<DocumentProcessingResponse> {
    const formData = new FormData();
    formData.append('application_id', applicationId);
    formData.append('document_type', documentType);
    formData.append('file', file);

    const response = await apiClient.post<DocumentProcessingResponse>(
      '/documents/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  }

  /**
   * Get processing status of a document.
   * 
   * @param documentId - Document unique identifier
   * @returns Promise resolving to document status response
   */
  static async getDocumentStatus(documentId: string): Promise<DocumentStatusResponse> {
    const response = await apiClient.get<DocumentStatusResponse>(
      `/documents/${documentId}/status`
    );

    return response.data;
  }

  /**
   * List all documents for an application.
   * 
   * @param applicationId - Application unique identifier
   * @returns Promise resolving to list of documents
   */
  static async listApplicationDocuments(
    applicationId: string
  ): Promise<DocumentProcessingResponse[]> {
    const response = await apiClient.get<DocumentProcessingResponse[]>(
      `/documents/application/${applicationId}`
    );

    return response.data;
  }

  /**
   * Validate extracted document data against application information.
   * 
   * @param documentId - Document unique identifier
   * @returns Promise resolving to validation response
   */
  static async validateDocument(documentId: string): Promise<DocumentValidationResponse> {
    const response = await apiClient.post<DocumentValidationResponse>(
      `/documents/${documentId}/validate`
    );

    return response.data;
  }

  /**
   * Delete a document and its associated file.
   * 
   * @param documentId - Document unique identifier
   * @returns Promise resolving when deletion is complete
   */
  static async deleteDocument(documentId: string): Promise<void> {
    await apiClient.delete(`/documents/${documentId}`);
  }

  /**
   * Poll document status until processing is complete.
   * Useful for showing real-time processing updates to users.
   * 
   * @param documentId - Document unique identifier
   * @param onStatusUpdate - Callback for status updates
   * @param maxAttempts - Maximum polling attempts (default: 30)
   * @param interval - Polling interval in milliseconds (default: 2000)
   * @returns Promise resolving to final document status
   */
  static async pollDocumentStatus(
    documentId: string,
    onStatusUpdate?: (status: DocumentStatusResponse) => void,
    maxAttempts: number = 30,
    interval: number = 2000
  ): Promise<DocumentStatusResponse> {
    let attempts = 0;
    
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          attempts++;
          const status = await this.getDocumentStatus(documentId);
          
          // Call status update callback if provided
          if (onStatusUpdate) {
            onStatusUpdate(status);
          }
          
          // Check if processing is complete
          if (status.processing_status === 'completed' || status.processing_status === 'failed') {
            resolve(status);
            return;
          }
          
          // Check if max attempts reached
          if (attempts >= maxAttempts) {
            reject(new Error('Polling timeout: Document processing took too long'));
            return;
          }
          
          // Continue polling
          setTimeout(poll, interval);
          
        } catch (error) {
          reject(error);
        }
      };
      
      // Start polling
      poll();
    });
  }

  /**
   * Upload document with progress tracking.
   * 
   * @param applicationId - Application ID this document belongs to
   * @param documentType - Type of document being uploaded
   * @param file - File to upload
   * @param onProgress - Progress callback function
   * @returns Promise resolving to document processing response
   */
  static async uploadDocumentWithProgress(
    applicationId: string,
    documentType: DocumentType,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<DocumentProcessingResponse> {
    const formData = new FormData();
    formData.append('application_id', applicationId);
    formData.append('document_type', documentType);
    formData.append('file', file);

    const response = await apiClient.post<DocumentProcessingResponse>(
      '/documents/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        },
      }
    );

    return response.data;
  }
}

// Export default instance
export const documentService = DocumentService;
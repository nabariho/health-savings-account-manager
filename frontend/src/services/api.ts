/**
 * Base API client configuration.
 * 
 * Provides configured axios instance with interceptors for error handling,
 * request/response transformation, and authentication.
 */

import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import type { ApiErrorResponse } from '@/types';

/**
 * API base URL from environment or default to development server.
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * Create configured axios instance.
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor to add authentication headers and logging.
 */
apiClient.interceptors.request.use(
  (config) => {
    // Log request in development
    if (import.meta.env.DEV) {
      console.log(`🔵 ${config.method?.toUpperCase()} ${config.url}`, config.data);
    }
    
    // Add authentication headers here if needed
    // const token = localStorage.getItem('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

/**
 * Response interceptor for error handling and logging.
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log successful response in development
    if (import.meta.env.DEV) {
      console.log(`🟢 ${response.status} ${response.config.url}`, response.data);
    }
    return response;
  },
  (error: AxiosError<ApiErrorResponse>) => {
    // Log error in development
    if (import.meta.env.DEV) {
      console.error(`🔴 ${error.response?.status} ${error.config?.url}`, error.response?.data);
    }
    
    // Handle specific error cases
    if (error.response?.status === 401) {
      // Handle authentication errors
      // Could redirect to login page or refresh token
    } else if (error.response?.status >= 500) {
      // Handle server errors
      console.error('Server error:', error.response?.data?.message);
    }
    
    return Promise.reject(error);
  }
);

/**
 * Generic API error class.
 */
export class ApiError extends Error {
  public readonly statusCode: number;
  public readonly originalError: AxiosError;
  
  constructor(error: AxiosError<ApiErrorResponse>) {
    const message = error.response?.data?.message || error.message || 'An unexpected error occurred';
    super(message);
    
    this.name = 'ApiError';
    this.statusCode = error.response?.status || 500;
    this.originalError = error;
  }
}

/**
 * Handle API errors and convert to ApiError instances.
 */
export const handleApiError = (error: unknown): ApiError => {
  if (axios.isAxiosError(error)) {
    return new ApiError(error);
  }
  
  // Handle non-axios errors
  return new ApiError({
    message: error instanceof Error ? error.message : 'Unknown error',
  } as AxiosError<ApiErrorResponse>);
};

export default apiClient;
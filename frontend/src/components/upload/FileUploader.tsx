/**
 * File uploader component for document uploads.
 * 
 * Provides drag-and-drop file upload functionality with progress tracking,
 * file validation, and preview capabilities.
 */

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import type { DocumentType, UploadProgress } from '../../types';

interface FileUploaderProps {
  /** Type of document being uploaded */
  documentType: DocumentType;
  /** Callback when file is selected */
  onFileSelect: (file: File) => void;
  /** Callback when upload starts */
  onUploadStart?: () => void;
  /** Upload progress information */
  uploadProgress?: UploadProgress;
  /** Whether uploader is disabled */
  disabled?: boolean;
  /** Custom class name */
  className?: string;
}

/**
 * FileUploader component for document uploads.
 */
export const FileUploader: React.FC<FileUploaderProps> = ({
  documentType,
  onFileSelect,
  onUploadStart,
  uploadProgress,
  disabled = false,
  className = '',
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Validate file type and size
  const validateFile = useCallback((file: File): string | null => {
    const allowedTypes = [
      'image/jpeg',
      'image/jpg', 
      'image/png',
      'image/webp',
      'image/gif',
      'application/pdf'
    ];

    if (!allowedTypes.includes(file.type)) {
      return 'Please select a valid image file (JPEG, PNG, WebP, GIF) or PDF document.';
    }

    // Max file size: 10MB
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      return 'File size must be less than 10MB.';
    }

    return null;
  }, []);

  // Handle file drop
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      const error = validateFile(file);
      
      if (error) {
        alert(error); // In production, use proper error handling
        return;
      }

      setSelectedFile(file);
      onFileSelect(file);
      
      if (onUploadStart) {
        onUploadStart();
      }
    }
  }, [onFileSelect, onUploadStart, validateFile]);

  // Configure dropzone
  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragReject,
  } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.webp', '.gif'],
      'application/pdf': ['.pdf']
    },
    multiple: false,
    disabled,
  });

  // Get document type display name
  const getDocumentTypeLabel = () => {
    switch (documentType) {
      case 'government_id':
        return 'Government ID';
      case 'employer_document':
        return 'Employer Document';
      default:
        return 'Document';
    }
  };

  // Get upload status text
  const getUploadStatusText = () => {
    if (!uploadProgress) return null;

    if (uploadProgress.error) {
      return `Upload failed: ${uploadProgress.error}`;
    }

    if (uploadProgress.complete) {
      return 'Upload complete!';
    }

    return `Uploading... ${uploadProgress.progress}%`;
  };

  return (
    <div className={`w-full ${className}`}>
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer
          ${isDragActive 
            ? 'border-blue-400 bg-blue-50' 
            : isDragReject 
            ? 'border-red-400 bg-red-50' 
            : disabled
            ? 'border-gray-300 bg-gray-100 cursor-not-allowed'
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
          }
        `}
      >
        <input {...getInputProps()} />
        
        {/* Upload Icon */}
        <div className="mb-4">
          <svg
            className={`mx-auto h-12 w-12 ${
              isDragReject ? 'text-red-400' : 'text-gray-400'
            }`}
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>

        {/* Upload Text */}
        <div className="mb-4">
          <p className="text-lg font-medium text-gray-900 mb-2">
            Upload {getDocumentTypeLabel()}
          </p>
          
          {isDragActive ? (
            <p className="text-blue-600">
              Drop the file here...
            </p>
          ) : isDragReject ? (
            <p className="text-red-600">
              File type not supported
            </p>
          ) : disabled ? (
            <p className="text-gray-500">
              Upload disabled
            </p>
          ) : (
            <>
              <p className="text-gray-600 mb-1">
                Drag and drop a file here, or click to select
              </p>
              <p className="text-sm text-gray-500">
                Supported formats: JPEG, PNG, WebP, GIF, PDF (max 10MB)
              </p>
            </>
          )}
        </div>

        {/* Upload Progress */}
        {uploadProgress && (
          <div className="mb-4">
            <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${
                  uploadProgress.error 
                    ? 'bg-red-500' 
                    : uploadProgress.complete 
                    ? 'bg-green-500' 
                    : 'bg-blue-500'
                }`}
                style={{ width: `${uploadProgress.progress}%` }}
              />
            </div>
            <p className={`text-sm ${
              uploadProgress.error 
                ? 'text-red-600' 
                : uploadProgress.complete 
                ? 'text-green-600' 
                : 'text-blue-600'
            }`}>
              {getUploadStatusText()}
            </p>
          </div>
        )}

        {/* Selected File Info */}
        {selectedFile && !uploadProgress?.complete && (
          <div className="mt-4 p-3 bg-gray-100 rounded-lg">
            <p className="text-sm font-medium text-gray-900">
              {selectedFile.name}
            </p>
            <p className="text-sm text-gray-600">
              {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
        )}
      </div>

      {/* Document Type Specific Instructions */}
      <div className="mt-4 p-4 bg-blue-50 rounded-lg">
        <h4 className="text-sm font-medium text-blue-900 mb-2">
          {getDocumentTypeLabel()} Requirements:
        </h4>
        <ul className="text-sm text-blue-800 space-y-1">
          {documentType === 'government_id' ? (
            <>
              <li>• Clear, readable photo of your government-issued ID</li>
              <li>• Full document visible (all four corners)</li>
              <li>• High resolution, no blur or glare</li>
              <li>• Valid, unexpired document</li>
            </>
          ) : (
            <>
              <li>• Recent employment verification document</li>
              <li>• Clear, readable text</li>
              <li>• Full document visible</li>
              <li>• Should show your name and employer information</li>
            </>
          )}
        </ul>
      </div>
    </div>
  );
};
/**
 * Document upload page component.
 * 
 * Provides interface for uploading and processing government ID and employer documents
 * with real-time status updates and validation results.
 */

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { FileUploader } from '../components/upload/FileUploader';
import { documentService } from '../services/documentService';
import { applicationService } from '../services/applicationService';
import type {
  DocumentType,
  DocumentProcessingResponse,
  DocumentValidationResponse,
  UploadProgress,
  GovernmentIdData,
  EmployerDocumentData,
} from '../types';

/**
 * DocumentUploadPage component for handling document uploads.
 */
export const DocumentUploadPage: React.FC = () => {
  const { applicationId } = useParams<{ applicationId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // State management
  const [selectedDocumentType, setSelectedDocumentType] = useState<DocumentType>('government_id');
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);
  const [processingDocumentId, setProcessingDocumentId] = useState<string | null>(null);
  const [validationResult, setValidationResult] = useState<DocumentValidationResponse | null>(null);

  // Fetch application data
  const { data: application, isLoading: applicationLoading } = useQuery({
    queryKey: ['application', applicationId],
    queryFn: () => applicationService.getApplication(applicationId!),
    enabled: !!applicationId,
  });

  // Fetch existing documents
  const { data: documents, isLoading: documentsLoading, refetch: refetchDocuments } = useQuery({
    queryKey: ['documents', applicationId],
    queryFn: () => documentService.listApplicationDocuments(applicationId!),
    enabled: !!applicationId,
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (params: { file: File; documentType: DocumentType }) => {
      const response = await documentService.uploadDocumentWithProgress(
        applicationId!,
        params.documentType,
        params.file,
        (progress) => {
          setUploadProgress({ progress, complete: false });
        }
      );
      
      setUploadProgress({ progress: 100, complete: true });
      return response;
    },
    onSuccess: async (response) => {
      setProcessingDocumentId(response.id);
      
      // Poll for processing completion
      try {
        await documentService.pollDocumentStatus(
          response.id,
          (status) => {
            // Could update UI with processing status here
            console.log('Processing status:', status.processing_status);
          }
        );
        
        // Refetch documents list
        await refetchDocuments();
        
        // Clear processing state
        setProcessingDocumentId(null);
        setUploadProgress(null);
        
      } catch (error) {
        console.error('Processing polling failed:', error);
        setProcessingDocumentId(null);
      }
    },
    onError: (error) => {
      console.error('Upload failed:', error);
      setUploadProgress({ 
        progress: 0, 
        complete: false, 
        error: error instanceof Error ? error.message : 'Upload failed' 
      });
    },
  });

  // Validation mutation
  const validateMutation = useMutation({
    mutationFn: (documentId: string) => documentService.validateDocument(documentId),
    onSuccess: (result) => {
      setValidationResult(result);
    },
  });

  // Handle file selection
  const handleFileSelect = (file: File) => {
    uploadMutation.mutate({ file, documentType: selectedDocumentType });
  };

  // Handle document validation
  const handleValidateDocument = (documentId: string) => {
    validateMutation.mutate(documentId);
  };

  // Handle document deletion
  const handleDeleteDocument = async (documentId: string) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await documentService.deleteDocument(documentId);
        await refetchDocuments();
      } catch (error) {
        console.error('Failed to delete document:', error);
      }
    }
  };

  // Navigate to next step
  const handleContinue = () => {
    navigate(`/applications/${applicationId}/qa`);
  };

  // Check if we have required documents
  const hasGovernmentId = documents?.some(d => d.document_type === 'government_id' && d.processing_status === 'completed');
  const hasEmployerDoc = documents?.some(d => d.document_type === 'employer_document' && d.processing_status === 'completed');
  const canContinue = hasGovernmentId; // Government ID is required, employer doc is optional

  if (applicationLoading) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  if (!application) {
    return (
      <Layout>
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Application Not Found</h1>
          <Button onClick={() => navigate('/')}>Return Home</Button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Document Upload
          </h1>
          <p className="text-lg text-gray-600">
            Upload your identification and employment documents for verification
          </p>
        </div>

        {/* Progress Indicator */}
        <div className="flex items-center justify-center space-x-4 mb-8">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center text-sm font-medium">
              ✓
            </div>
            <span className="ml-2 text-sm text-gray-600">Personal Info</span>
          </div>
          <div className="w-16 h-0.5 bg-blue-500"></div>
          <div className="flex items-center">
            <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-medium">
              2
            </div>
            <span className="ml-2 text-sm font-medium text-blue-600">Documents</span>
          </div>
          <div className="w-16 h-0.5 bg-gray-300"></div>
          <div className="flex items-center">
            <div className="w-8 h-8 bg-gray-300 text-gray-600 rounded-full flex items-center justify-center text-sm font-medium">
              3
            </div>
            <span className="ml-2 text-sm text-gray-600">Q&A</span>
          </div>
          <div className="w-16 h-0.5 bg-gray-300"></div>
          <div className="flex items-center">
            <div className="w-8 h-8 bg-gray-300 text-gray-600 rounded-full flex items-center justify-center text-sm font-medium">
              4
            </div>
            <span className="ml-2 text-sm text-gray-600">Decision</span>
          </div>
        </div>

        {/* Document Type Selection */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Select Document Type
          </h2>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={() => setSelectedDocumentType('government_id')}
                className={`p-4 border rounded-lg text-left transition-colors ${
                  selectedDocumentType === 'government_id'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <h3 className="font-medium text-gray-900">Government ID</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Driver's license, passport, or state ID
                </p>
                <p className="text-xs text-red-600 mt-1">* Required</p>
              </button>
              
              <button
                onClick={() => setSelectedDocumentType('employer_document')}
                className={`p-4 border rounded-lg text-left transition-colors ${
                  selectedDocumentType === 'employer_document'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <h3 className="font-medium text-gray-900">Employer Document</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Pay stub, employment letter, or benefits summary
                </p>
                <p className="text-xs text-gray-600 mt-1">Optional</p>
              </button>
            </div>
          </div>
        </Card>

        {/* File Upload */}
        <Card className="p-6">
          <FileUploader
            documentType={selectedDocumentType}
            onFileSelect={handleFileSelect}
            uploadProgress={uploadProgress || undefined}
            disabled={uploadMutation.isPending || !!processingDocumentId}
          />
        </Card>

        {/* Existing Documents */}
        {documents && documents.length > 0 && (
          <Card className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Uploaded Documents
            </h2>
            <div className="space-y-4">
              {documents.map((doc) => (
                <DocumentCard
                  key={doc.id}
                  document={doc}
                  onValidate={() => handleValidateDocument(doc.id)}
                  onDelete={() => handleDeleteDocument(doc.id)}
                  isValidating={validateMutation.isPending}
                />
              ))}
            </div>
          </Card>
        )}

        {/* Validation Results */}
        {validationResult && (
          <Card className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Validation Results
            </h2>
            <ValidationResultDisplay result={validationResult} />
          </Card>
        )}

        {/* Navigation */}
        <div className="flex justify-between pt-6">
          <Button
            onClick={() => navigate(`/applications/${applicationId}`)}
            variant="outline"
          >
            Back to Application
          </Button>
          
          <Button
            onClick={handleContinue}
            disabled={!canContinue}
          >
            Continue to Q&A
          </Button>
        </div>
      </div>
    </Layout>
  );
};

/**
 * Document card component for displaying uploaded documents.
 */
interface DocumentCardProps {
  document: DocumentProcessingResponse;
  onValidate: () => void;
  onDelete: () => void;
  isValidating: boolean;
}

const DocumentCard: React.FC<DocumentCardProps> = ({
  document,
  onValidate,
  onDelete,
  isValidating,
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'processing': return 'text-yellow-600 bg-yellow-100';
      case 'failed': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getDocumentTypeLabel = (type: DocumentType) => {
    return type === 'government_id' ? 'Government ID' : 'Employer Document';
  };

  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-medium text-gray-900">
          {getDocumentTypeLabel(document.document_type)}
        </h3>
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(document.processing_status)}`}>
            {document.processing_status}
          </span>
          {document.processing_status === 'completed' && (
            <Button
              size="sm"
              onClick={onValidate}
              disabled={isValidating}
            >
              {isValidating ? 'Validating...' : 'Validate'}
            </Button>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={onDelete}
          >
            Delete
          </Button>
        </div>
      </div>
      
      <p className="text-sm text-gray-600 mb-2">{document.file_name}</p>
      
      {document.processing_error && (
        <p className="text-sm text-red-600 mb-2">
          Error: {document.processing_error}
        </p>
      )}
      
      {document.extracted_data && (
        <div className="mt-2 p-3 bg-gray-50 rounded">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Extracted Data:</h4>
          <ExtractedDataDisplay 
            data={document.extracted_data as GovernmentIdData | EmployerDocumentData} 
            documentType={document.document_type}
          />
        </div>
      )}
    </div>
  );
};

/**
 * Component for displaying extracted document data.
 */
interface ExtractedDataDisplayProps {
  data: GovernmentIdData | EmployerDocumentData;
  documentType: DocumentType;
}

const ExtractedDataDisplay: React.FC<ExtractedDataDisplayProps> = ({ data, documentType }) => {
  if (documentType === 'government_id') {
    const govIdData = data as GovernmentIdData;
    return (
      <div className="text-sm space-y-1">
        <p><span className="font-medium">Name:</span> {govIdData.full_name}</p>
        <p><span className="font-medium">DOB:</span> {govIdData.date_of_birth}</p>
        <p><span className="font-medium">ID Number:</span> {govIdData.id_number}</p>
        {govIdData.address_street && (
          <p><span className="font-medium">Address:</span> {govIdData.address_street}, {govIdData.address_city}, {govIdData.address_state} {govIdData.address_zip}</p>
        )}
      </div>
    );
  } else {
    const empData = data as EmployerDocumentData;
    return (
      <div className="text-sm space-y-1">
        <p><span className="font-medium">Employee:</span> {empData.employee_name}</p>
        <p><span className="font-medium">Employer:</span> {empData.employer_name}</p>
        {empData.document_date && (
          <p><span className="font-medium">Document Date:</span> {empData.document_date}</p>
        )}
      </div>
    );
  }
};

/**
 * Component for displaying validation results.
 */
interface ValidationResultDisplayProps {
  result: DocumentValidationResponse;
}

const ValidationResultDisplay: React.FC<ValidationResultDisplayProps> = ({ result }) => {
  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'APPROVE': return 'text-green-600 bg-green-100';
      case 'MANUAL_REVIEW': return 'text-yellow-600 bg-yellow-100';
      case 'REJECT': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">Overall Match Score</p>
          <p className="text-2xl font-bold text-gray-900">{(result.overall_match_score * 100).toFixed(1)}%</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRecommendationColor(result.recommendation)}`}>
          {result.recommendation}
        </span>
      </div>
      
      <div className="space-y-2">
        <h4 className="font-medium text-gray-900">Field Validation Results:</h4>
        {result.validation_results.map((validation, index) => (
          <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
            <div>
              <p className="text-sm font-medium text-gray-900">{validation.field_name}</p>
              {validation.reason && (
                <p className="text-xs text-gray-600">{validation.reason}</p>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">{(validation.confidence_score * 100).toFixed(0)}%</span>
              <span className={`w-3 h-3 rounded-full ${validation.is_match ? 'bg-green-500' : 'bg-red-500'}`}></span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
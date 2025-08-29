/**
 * Tests for FileUploader component.
 * 
 * Tests file upload functionality including drag-and-drop, file validation,
 * progress tracking, and error handling.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, type MockedFunction } from 'vitest';
import { FileUploader } from '../FileUploader';
import type { DocumentType, UploadProgress } from '../../../types';

// Mock react-dropzone
const mockUseDropzone = vi.fn();
vi.mock('react-dropzone', () => ({
  useDropzone: mockUseDropzone,
}));

describe('FileUploader', () => {
  const mockOnFileSelect = vi.fn();
  const mockOnUploadStart = vi.fn();

  const defaultProps = {
    documentType: 'government_id' as DocumentType,
    onFileSelect: mockOnFileSelect,
    onUploadStart: mockOnUploadStart,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // Reset mock to default behavior
    mockUseDropzone.mockReturnValue({
      getRootProps: () => ({}),
      getInputProps: () => ({}),
      isDragActive: false,
      isDragReject: false,
    });
  });

  it('renders correctly for government ID document type', () => {
    render(<FileUploader {...defaultProps} />);
    
    expect(screen.getByText('Upload Government ID')).toBeInTheDocument();
    expect(screen.getByText('Drag and drop a file here, or click to select')).toBeInTheDocument();
    expect(screen.getByText('Supported formats: JPEG, PNG, WebP, GIF, PDF (max 10MB)')).toBeInTheDocument();
  });

  it('renders correctly for employer document type', () => {
    render(<FileUploader {...defaultProps} documentType="employer_document" />);
    
    expect(screen.getByText('Upload Employer Document')).toBeInTheDocument();
  });

  it('displays government ID requirements', () => {
    render(<FileUploader {...defaultProps} />);
    
    expect(screen.getByText('Government ID Requirements:')).toBeInTheDocument();
    expect(screen.getByText('• Clear, readable photo of your government-issued ID')).toBeInTheDocument();
    expect(screen.getByText('• Full document visible (all four corners)')).toBeInTheDocument();
  });

  it('displays employer document requirements', () => {
    render(<FileUploader {...defaultProps} documentType="employer_document" />);
    
    expect(screen.getByText('Employer Document Requirements:')).toBeInTheDocument();
    expect(screen.getByText('• Recent employment verification document')).toBeInTheDocument();
  });

  it('shows upload progress when provided', () => {
    const uploadProgress: UploadProgress = {
      progress: 50,
      complete: false,
    };

    render(<FileUploader {...defaultProps} uploadProgress={uploadProgress} />);
    
    expect(screen.getByText('Uploading... 50%')).toBeInTheDocument();
    
    // Check progress bar
    const progressBar = screen.getByRole('progressbar', { hidden: true });
    expect(progressBar).toHaveStyle({ width: '50%' });
  });

  it('shows completion status when upload is complete', () => {
    const uploadProgress: UploadProgress = {
      progress: 100,
      complete: true,
    };

    render(<FileUploader {...defaultProps} uploadProgress={uploadProgress} />);
    
    expect(screen.getByText('Upload complete!')).toBeInTheDocument();
    
    // Check progress bar is green
    const progressBar = screen.getByRole('progressbar', { hidden: true });
    expect(progressBar).toHaveClass('bg-green-500');
  });

  it('shows error status when upload fails', () => {
    const uploadProgress: UploadProgress = {
      progress: 30,
      complete: false,
      error: 'Upload failed: Network error',
    };

    render(<FileUploader {...defaultProps} uploadProgress={uploadProgress} />);
    
    expect(screen.getByText('Upload failed: Upload failed: Network error')).toBeInTheDocument();
    
    // Check progress bar is red
    const progressBar = screen.getByRole('progressbar', { hidden: true });
    expect(progressBar).toHaveClass('bg-red-500');
  });

  it('is disabled when disabled prop is true', () => {
    render(<FileUploader {...defaultProps} disabled={true} />);
    
    expect(screen.getByText('Upload disabled')).toBeInTheDocument();
    
    // Check that the dropzone area has disabled styling
    const dropzone = screen.getByRole('button', { hidden: true });
    expect(dropzone).toHaveClass('cursor-not-allowed');
  });

  it('applies custom className', () => {
    const customClass = 'custom-uploader-class';
    render(<FileUploader {...defaultProps} className={customClass} />);
    
    const container = screen.getByText('Upload Government ID').closest('div');
    expect(container).toHaveClass(customClass);
  });

  it('calls onFileSelect when a valid file is selected', async () => {
    const { useDropzone } = await import('react-dropzone');
    const mockUseDropzone = useDropzone as jest.MockedFunction<typeof useDropzone>;
    
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
    
    // Mock the dropzone hook to simulate file drop
    mockUseDropzone.mockImplementation(({ onDrop }) => ({
      getRootProps: () => ({
        onClick: vi.fn(),
      }),
      getInputProps: () => ({}),
      isDragActive: false,
      isDragReject: false,
    }));

    render(<FileUploader {...defaultProps} />);
    
    // Simulate file drop by directly calling the onDrop callback
    const { onDrop } = mockUseDropzone.mock.calls[0][0];
    if (onDrop) {
      onDrop([file], [], { preventDefault: vi.fn(), stopPropagation: vi.fn() } as any);
    }

    await waitFor(() => {
      expect(mockOnFileSelect).toHaveBeenCalledWith(file);
      expect(mockOnUploadStart).toHaveBeenCalled();
    });
  });

  it('shows drag active state', () => {
    const { useDropzone } = require('react-dropzone');
    useDropzone.mockImplementation(() => ({
      getRootProps: () => ({}),
      getInputProps: () => ({}),
      isDragActive: true,
      isDragReject: false,
    }));

    render(<FileUploader {...defaultProps} />);
    
    expect(screen.getByText('Drop the file here...')).toBeInTheDocument();
    
    // Check for active drag styling
    const dropzone = screen.getByText('Drop the file here...').closest('div');
    expect(dropzone).toHaveClass('border-blue-400', 'bg-blue-50');
  });

  it('shows drag reject state', () => {
    const { useDropzone } = require('react-dropzone');
    useDropzone.mockImplementation(() => ({
      getRootProps: () => ({}),
      getInputProps: () => ({}),
      isDragActive: false,
      isDragReject: true,
    }));

    render(<FileUploader {...defaultProps} />);
    
    expect(screen.getByText('File type not supported')).toBeInTheDocument();
    
    // Check for reject styling
    const dropzone = screen.getByText('File type not supported').closest('div');
    expect(dropzone).toHaveClass('border-red-400', 'bg-red-50');
  });

  it('validates file type and shows error for invalid types', () => {
    // Create a spy for window.alert
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
    
    const { useDropzone } = require('react-dropzone');
    const mockOnDrop = vi.fn();
    
    useDropzone.mockImplementation(({ onDrop }) => {
      mockOnDrop.mockImplementation(onDrop);
      return {
        getRootProps: () => ({}),
        getInputProps: () => ({}),
        isDragActive: false,
        isDragReject: false,
      };
    });

    render(<FileUploader {...defaultProps} />);
    
    // Simulate dropping an invalid file type
    const invalidFile = new File(['test'], 'test.txt', { type: 'text/plain' });
    mockOnDrop([invalidFile]);

    expect(alertSpy).toHaveBeenCalledWith(
      expect.stringContaining('Please select a valid image file')
    );
    expect(mockOnFileSelect).not.toHaveBeenCalled();
    
    alertSpy.mockRestore();
  });

  it('validates file size and shows error for large files', () => {
    // Create a spy for window.alert
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
    
    const { useDropzone } = require('react-dropzone');
    const mockOnDrop = vi.fn();
    
    useDropzone.mockImplementation(({ onDrop }) => {
      mockOnDrop.mockImplementation(onDrop);
      return {
        getRootProps: () => ({}),
        getInputProps: () => ({}),
        isDragActive: false,
        isDragReject: false,
      };
    });

    render(<FileUploader {...defaultProps} />);
    
    // Create a large file (11MB)
    const largeFileData = new Array(11 * 1024 * 1024).fill('x').join('');
    const largeFile = new File([largeFileData], 'large.jpg', { type: 'image/jpeg' });
    
    // Mock file size since File constructor doesn't set actual size
    Object.defineProperty(largeFile, 'size', { value: 11 * 1024 * 1024 });
    
    mockOnDrop([largeFile]);

    expect(alertSpy).toHaveBeenCalledWith('File size must be less than 10MB.');
    expect(mockOnFileSelect).not.toHaveBeenCalled();
    
    alertSpy.mockRestore();
  });

  it('displays selected file information', () => {
    const { useDropzone } = require('react-dropzone');
    const mockOnDrop = vi.fn();
    
    useDropzone.mockImplementation(({ onDrop }) => {
      mockOnDrop.mockImplementation(onDrop);
      return {
        getRootProps: () => ({}),
        getInputProps: () => ({}),
        isDragActive: false,
        isDragReject: false,
      };
    });

    render(<FileUploader {...defaultProps} />);
    
    const file = new File(['test content'], 'test-id.jpg', { type: 'image/jpeg' });
    Object.defineProperty(file, 'size', { value: 1024 * 1024 }); // 1MB
    
    mockOnDrop([file]);

    expect(screen.getByText('test-id.jpg')).toBeInTheDocument();
    expect(screen.getByText('1.00 MB')).toBeInTheDocument();
  });

  it('hides file info when upload is complete', () => {
    const { useDropzone } = require('react-dropzone');
    const mockOnDrop = vi.fn();
    
    useDropzone.mockImplementation(({ onDrop }) => {
      mockOnDrop.mockImplementation(onDrop);
      return {
        getRootProps: () => ({}),
        getInputProps: () => ({}),
        isDragActive: false,
        isDragReject: false,
      };
    });

    const uploadProgress: UploadProgress = {
      progress: 100,
      complete: true,
    };

    render(<FileUploader {...defaultProps} uploadProgress={uploadProgress} />);
    
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
    mockOnDrop([file]);

    // File info should not be shown when upload is complete
    expect(screen.queryByText('test.jpg')).not.toBeInTheDocument();
  });
});
/**
 * Tests for CitationCard component.
 * 
 * Tests citation display functionality including document name, page number,
 * excerpt text, relevance score indicators, and visual formatting.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { CitationCard } from '../CitationCard';
import type { Citation } from '@/types/hsaAssistant';

describe('CitationCard', () => {
  const mockCitation: Citation = {
    document_name: 'IRS Publication 969',
    page_number: 15,
    excerpt: 'Health Savings Accounts (HSAs) are tax-advantaged accounts that can be used to pay for qualified medical expenses.',
    relevance_score: 0.85,
  };

  it('renders citation with all fields correctly', () => {
    render(<CitationCard citation={mockCitation} index={0} />);
    
    // Check document name
    expect(screen.getByText('IRS Publication 969')).toBeInTheDocument();
    
    // Check page number
    expect(screen.getByText('Page 15')).toBeInTheDocument();
    
    // Check excerpt
    expect(screen.getByText('Health Savings Accounts (HSAs) are tax-advantaged accounts that can be used to pay for qualified medical expenses.')).toBeInTheDocument();
    
    // Check relevance score
    expect(screen.getByText('85%')).toBeInTheDocument();
    
    // Check index number
    expect(screen.getByText('1')).toBeInTheDocument(); // index 0 displays as 1
  });

  it('renders citation without page number', () => {
    const citationWithoutPage: Citation = {
      document_name: 'HSA Guidelines',
      excerpt: 'Test excerpt without page number.',
      relevance_score: 0.75,
    };

    render(<CitationCard citation={citationWithoutPage} index={1} />);
    
    expect(screen.getByText('HSA Guidelines')).toBeInTheDocument();
    expect(screen.getByText('Test excerpt without page number.')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // index 1 displays as 2
    
    // Page number should not be displayed
    expect(screen.queryByText(/Page/)).not.toBeInTheDocument();
  });

  it('displays correct index number', () => {
    render(<CitationCard citation={mockCitation} index={5} />);
    
    expect(screen.getByText('6')).toBeInTheDocument(); // index 5 displays as 6
  });

  it('displays high relevance score with green indicator', () => {
    const highRelevanceCitation: Citation = {
      document_name: 'Test Document',
      excerpt: 'High relevance excerpt.',
      relevance_score: 0.95, // 95%
    };

    render(<CitationCard citation={highRelevanceCitation} index={0} />);
    
    expect(screen.getByText('95%')).toBeInTheDocument();
    
    // Check for green relevance indicator
    const relevanceIndicator = screen.getByText('95%').previousElementSibling;
    expect(relevanceIndicator).toHaveClass('bg-green-400');
  });

  it('displays medium relevance score with yellow indicator', () => {
    const mediumRelevanceCitation: Citation = {
      document_name: 'Test Document',
      excerpt: 'Medium relevance excerpt.',
      relevance_score: 0.70, // 70%
    };

    render(<CitationCard citation={mediumRelevanceCitation} index={0} />);
    
    expect(screen.getByText('70%')).toBeInTheDocument();
    
    // Check for yellow relevance indicator
    const relevanceIndicator = screen.getByText('70%').previousElementSibling;
    expect(relevanceIndicator).toHaveClass('bg-yellow-400');
  });

  it('displays low relevance score with gray indicator', () => {
    const lowRelevanceCitation: Citation = {
      document_name: 'Test Document',
      excerpt: 'Low relevance excerpt.',
      relevance_score: 0.45, // 45%
    };

    render(<CitationCard citation={lowRelevanceCitation} index={0} />);
    
    expect(screen.getByText('45%')).toBeInTheDocument();
    
    // Check for gray relevance indicator
    const relevanceIndicator = screen.getByText('45%').previousElementSibling;
    expect(relevanceIndicator).toHaveClass('bg-gray-400');
  });

  it('rounds relevance score to nearest integer', () => {
    const fractionalRelevanceCitation: Citation = {
      document_name: 'Test Document',
      excerpt: 'Fractional relevance excerpt.',
      relevance_score: 0.876, // Should round to 88%
    };

    render(<CitationCard citation={fractionalRelevanceCitation} index={0} />);
    
    expect(screen.getByText('88%')).toBeInTheDocument();
  });

  it('handles zero relevance score', () => {
    const zeroRelevanceCitation: Citation = {
      document_name: 'Test Document',
      excerpt: 'Zero relevance excerpt.',
      relevance_score: 0.0,
    };

    render(<CitationCard citation={zeroRelevanceCitation} index={0} />);
    
    expect(screen.getByText('0%')).toBeInTheDocument();
    
    // Should use gray indicator for 0%
    const relevanceIndicator = screen.getByText('0%').previousElementSibling;
    expect(relevanceIndicator).toHaveClass('bg-gray-400');
  });

  it('handles maximum relevance score', () => {
    const maxRelevanceCitation: Citation = {
      document_name: 'Test Document',
      excerpt: 'Perfect relevance excerpt.',
      relevance_score: 1.0, // 100%
    };

    render(<CitationCard citation={maxRelevanceCitation} index={0} />);
    
    expect(screen.getByText('100%')).toBeInTheDocument();
    
    // Should use green indicator for 100%
    const relevanceIndicator = screen.getByText('100%').previousElementSibling;
    expect(relevanceIndicator).toHaveClass('bg-green-400');
  });

  it('has proper styling and structure', () => {
    render(<CitationCard citation={mockCitation} index={0} />);
    
    // Check main container styling
    const container = screen.getByText('IRS Publication 969').closest('div');
    expect(container).toHaveClass('bg-white', 'border', 'border-gray-200', 'rounded-md', 'p-3', 'text-sm');
  });

  it('displays index badge with proper styling', () => {
    render(<CitationCard citation={mockCitation} index={2} />);
    
    const indexBadge = screen.getByText('3');
    expect(indexBadge).toHaveClass(
      'inline-flex',
      'items-center',
      'justify-center',
      'w-5',
      'h-5',
      'text-xs',
      'font-medium',
      'text-primary-600',
      'bg-primary-100',
      'rounded-full'
    );
  });

  it('handles very long document names', () => {
    const longNameCitation: Citation = {
      document_name: 'Very Long Document Name That Might Overflow The Container And Cause Layout Issues',
      excerpt: 'Test excerpt.',
      relevance_score: 0.5,
    };

    render(<CitationCard citation={longNameCitation} index={0} />);
    
    expect(screen.getByText('Very Long Document Name That Might Overflow The Container And Cause Layout Issues')).toBeInTheDocument();
  });

  it('handles very long excerpts', () => {
    const longExcerptCitation: Citation = {
      document_name: 'Test Document',
      excerpt: 'This is a very long excerpt that contains multiple sentences and should wrap properly within the citation card container. It includes detailed information about HSA rules and regulations that might span several lines when displayed in the user interface.',
      relevance_score: 0.8,
    };

    render(<CitationCard citation={longExcerptCitation} index={0} />);
    
    expect(screen.getByText(/This is a very long excerpt/)).toBeInTheDocument();
    
    // Check that excerpt text has proper styling for line wrapping
    const excerptDiv = screen.getByText(/This is a very long excerpt/).closest('div');
    expect(excerptDiv).toHaveClass('text-gray-700', 'text-sm', 'leading-relaxed');
  });

  it('handles special characters in document name and excerpt', () => {
    const specialCharsCitation: Citation = {
      document_name: 'IRS Pub. #969 (Rev. 2024) - HSA Rules & Regulations',
      excerpt: 'Special characters: $, %, &, <, >, ", \', and other symbols should be displayed correctly.',
      relevance_score: 0.9,
    };

    render(<CitationCard citation={specialCharsCitation} index={0} />);
    
    expect(screen.getByText('IRS Pub. #969 (Rev. 2024) - HSA Rules & Regulations')).toBeInTheDocument();
    expect(screen.getByText('Special characters: $, %, &, <, >, ", \', and other symbols should be displayed correctly.')).toBeInTheDocument();
  });

  it('displays page number with proper formatting', () => {
    const pageNumberCitation: Citation = {
      document_name: 'Test Document',
      page_number: 123,
      excerpt: 'Test excerpt with large page number.',
      relevance_score: 0.7,
    };

    render(<CitationCard citation={pageNumberCitation} index={0} />);
    
    const pageText = screen.getByText('Page 123');
    expect(pageText).toHaveClass('text-xs', 'text-gray-500');
  });

  it('maintains correct layout structure', () => {
    render(<CitationCard citation={mockCitation} index={0} />);
    
    // Check header structure with document info and relevance score
    const headerDiv = screen.getByText('IRS Publication 969').closest('.flex');
    expect(headerDiv).toHaveClass('flex', 'items-start', 'justify-between', 'mb-2');
    
    // Check that relevance score is in the right section
    const relevanceDiv = screen.getByText('85%').closest('.flex');
    expect(relevanceDiv).toHaveClass('flex', 'items-center');
  });

  it('boundary test for relevance score thresholds', () => {
    // Test exact boundary values
    const boundaryTests = [
      { score: 0.79, expectedColor: 'bg-yellow-400' }, // Just below 80%
      { score: 0.80, expectedColor: 'bg-green-400' },   // Exactly 80%
      { score: 0.59, expectedColor: 'bg-gray-400' },    // Just below 60%
      { score: 0.60, expectedColor: 'bg-yellow-400' },  // Exactly 60%
    ];

    boundaryTests.forEach(({ score, expectedColor }, testIndex) => {
      const citation: Citation = {
        document_name: `Test Document ${testIndex}`,
        excerpt: `Test excerpt ${testIndex}.`,
        relevance_score: score,
      };

      const { container } = render(<CitationCard citation={citation} index={testIndex} />);
      
      const relevanceIndicator = screen.getByText(`${Math.round(score * 100)}%`).previousElementSibling;
      expect(relevanceIndicator).toHaveClass(expectedColor);
      
      // Clean up for next test
      container.remove();
    });
  });
});
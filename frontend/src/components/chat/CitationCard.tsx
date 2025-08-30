/**
 * CitationCard component for displaying source citations.
 * 
 * Shows citation information including document name, page number,
 * excerpt text, and relevance score in a compact card format.
 */

import React from 'react';
import clsx from 'clsx';
import type { CitationProps } from '@/types/hsaAssistant';

/**
 * CitationCard component.
 */
export const CitationCard: React.FC<CitationProps> = ({ citation, index }) => {
  const relevancePercentage = Math.round(citation.relevance_score * 100);

  return (
    <div className="bg-white border border-gray-200 rounded-md p-3 text-sm">
      {/* Header with document info */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-medium text-primary-600 bg-primary-100 rounded-full">
            {index + 1}
          </span>
          <div>
            <div className="font-medium text-gray-900">
              {citation.document_name}
            </div>
            {citation.page_number && (
              <div className="text-xs text-gray-500">
                Page {citation.page_number}
              </div>
            )}
          </div>
        </div>
        
        {/* Relevance score */}
        <div className="flex items-center space-x-1">
          <div className="flex items-center">
            <div
              className={clsx(
                'w-2 h-2 rounded-full',
                relevancePercentage >= 80
                  ? 'bg-green-400'
                  : relevancePercentage >= 60
                  ? 'bg-yellow-400'
                  : 'bg-gray-400'
              )}
            />
            <span className="text-xs text-gray-500 ml-1">
              {relevancePercentage}%
            </span>
          </div>
        </div>
      </div>

      {/* Citation excerpt */}
      <div className="text-gray-700 text-sm leading-relaxed">
        {citation.excerpt}
      </div>
    </div>
  );
};

export default CitationCard;
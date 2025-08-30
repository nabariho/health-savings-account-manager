/**
 * MessageList component for displaying chat messages.
 * 
 * Renders a scrollable list of chat messages with support for
 * user messages, assistant responses, citations, and loading states.
 */

import React, { useEffect, useRef } from 'react';
import clsx from 'clsx';
import type { MessageListProps, ChatMessage } from '@/types/hsaAssistant';
import { CitationCard } from './CitationCard';

/**
 * Individual message component.
 */
interface MessageItemProps {
  message: ChatMessage;
  onRetry?: (messageId: string) => void;
}

const MessageItem: React.FC<MessageItemProps> = ({ message, onRetry }) => {
  const isUser = message.role === 'user';
  const isError = message.status === 'error';
  const isLoading = message.status === 'sending';

  return (
    <div
      className={clsx(
        'flex w-full mb-4',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={clsx(
          'max-w-[80%] rounded-lg px-4 py-3 shadow-sm',
          isUser
            ? 'bg-primary-600 text-white'
            : isError
            ? 'bg-red-50 border border-red-200'
            : 'bg-gray-100 border border-gray-200',
          isLoading && 'opacity-60'
        )}
      >
        {/* Message content */}
        <div className={clsx(
          'whitespace-pre-wrap break-words',
          isUser ? 'text-white' : isError ? 'text-red-700' : 'text-gray-900'
        )}>
          {message.content}
        </div>

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex items-center mt-2 text-sm text-gray-500">
            <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-primary-600 mr-2"></div>
            Sending...
          </div>
        )}

        {/* Error state with retry button */}
        {isError && onRetry && (
          <div className="mt-2 flex items-center gap-2">
            <button
              onClick={() => onRetry(message.id)}
              className="text-sm text-red-600 hover:text-red-800 underline"
            >
              Retry
            </button>
          </div>
        )}

        {/* Confidence score for assistant messages */}
        {!isUser && message.confidence_score !== undefined && !isError && (
          <div className="mt-2 text-xs text-gray-500">
            Confidence: {(message.confidence_score * 100).toFixed(0)}%
          </div>
        )}

        {/* Citations for assistant messages */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="mt-3">
            <div className="text-xs font-medium text-gray-700 mb-2">
              Sources:
            </div>
            <div className="space-y-2">
              {message.citations.map((citation, index) => (
                <CitationCard
                  key={index}
                  citation={citation}
                  index={index}
                />
              ))}
            </div>
          </div>
        )}

        {/* Timestamp */}
        <div className={clsx(
          'mt-2 text-xs',
          isUser ? 'text-primary-100' : 'text-gray-500'
        )}>
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

/**
 * Loading dots component for when assistant is thinking.
 */
const LoadingDots: React.FC = () => (
  <div className="flex justify-start w-full mb-4">
    <div className="bg-gray-100 border border-gray-200 rounded-lg px-4 py-3 shadow-sm">
      <div className="flex items-center space-x-1">
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
        </div>
        <span className="text-sm text-gray-500 ml-2">HSA Assistant is thinking...</span>
      </div>
    </div>
  </div>
);

/**
 * Empty state component.
 */
const EmptyState: React.FC = () => (
  <div className="flex flex-col items-center justify-center h-full text-center py-12">
    <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4">
      <svg
        className="w-8 h-8 text-primary-600"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
        />
      </svg>
    </div>
    <h3 className="text-lg font-medium text-gray-900 mb-2">
      Welcome to HSA Assistant
    </h3>
    <p className="text-gray-500 max-w-sm">
      Ask me any questions about Health Savings Accounts, contribution limits, 
      eligibility requirements, or qualified expenses.
    </p>
  </div>
);

/**
 * MessageList component.
 */
export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading = false,
  className,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleRetry = (messageId: string) => {
    // This would typically be passed down from parent or context
    console.log('Retry message:', messageId);
  };

  return (
    <div
      className={clsx(
        'flex-1 overflow-y-auto px-4 py-6 space-y-4',
        className
      )}
    >
      {/* Empty state */}
      {messages.length === 0 && !isLoading && <EmptyState />}

      {/* Messages */}
      {messages.map((message) => (
        <MessageItem
          key={message.id}
          message={message}
          onRetry={handleRetry}
        />
      ))}

      {/* Loading indicator */}
      {isLoading && <LoadingDots />}

      {/* Scroll anchor */}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
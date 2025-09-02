/**
 * MessageList component for displaying chat messages.
 * 
 * Renders a scrollable list of chat messages with support for
 * user messages, assistant responses, citations, rich text formatting,
 * and interactive message actions.
 */

import React, { useEffect, useRef } from 'react';
import clsx from 'clsx';
import type { MessageListProps, ChatMessage } from '@/types/hsaAssistant';
import { useChat } from '@/contexts/ChatContext';
import { useToastActions } from '@/components/ui/Toast';
import { MessageBubble } from './MessageBubble';
import { RichTextRenderer } from './RichTextRenderer';
import { MessageActions } from './MessageActions';
import { CitationCard } from './CitationCard';

/**
 * Individual message component with enhanced features.
 */
interface MessageItemProps {
  message: ChatMessage;
}

const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
  const {
    copyMessage,
    regenerateResponse,
    provideFeedback,
    shareMessage,
    retryMessage,
  } = useChat();
  
  const toast = useToastActions();
  
  const isUser = message.role === 'user';
  const isError = message.status === 'error';

  /**
   * Handle copy action with toast feedback.
   */
  const handleCopy = async () => {
    await copyMessage(message.id);
    toast.success('Message copied to clipboard!');
  };

  /**
   * Handle regenerate action.
   */
  const handleRegenerate = async (messageId: string) => {
    await regenerateResponse(messageId);
    toast.info('Regenerating response...');
  };

  /**
   * Handle feedback action.
   */
  const handleFeedback = async (messageId: string, feedback: 'up' | 'down') => {
    await provideFeedback(messageId, feedback);
    toast.success(
      feedback === 'up' 
        ? 'Thanks for the positive feedback!' 
        : 'Thanks for the feedback, we\'ll work to improve!'
    );
  };

  /**
   * Handle share action.
   */
  const handleShare = async (messageId: string) => {
    await shareMessage(messageId);
    if ('share' in navigator) {
      toast.info('Message shared successfully!');
    } else {
      toast.success('Message copied to clipboard for sharing!');
    }
  };

  /**
   * Handle retry for error messages.
   */
  const handleRetry = async () => {
    if (isUser) {
      await retryMessage(message.id);
    }
  };

  return (
    <div className="relative group">
      <MessageBubble message={message} showAvatar>
        {/* Message content with rich text formatting */}
        {message.richText !== false ? (
          <RichTextRenderer 
            content={message.content} 
            compact={isUser}
          />
        ) : (
          <div className="whitespace-pre-wrap break-words">
            {message.content}
          </div>
        )}

        {/* Error state with retry button */}
        {isError && isUser && (
          <div className="mt-2 flex items-center gap-2">
            <button
              onClick={handleRetry}
              className="text-sm text-red-100 hover:text-white underline"
            >
              Retry
            </button>
          </div>
        )}

        {/* Citations for assistant messages */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="mt-4">
            <details className="group/citations">
              <summary className="cursor-pointer text-xs font-medium text-gray-600 hover:text-gray-800 mb-2 flex items-center">
                <span>Sources ({message.citations.length})</span>
                <svg 
                  className="w-4 h-4 ml-1 transform group-open/citations:rotate-90 transition-transform duration-200" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </summary>
              <div className="space-y-2 mt-2">
                {message.citations.map((citation, index) => (
                  <CitationCard
                    key={index}
                    citation={citation}
                    index={index}
                  />
                ))}
              </div>
            </details>
          </div>
        )}
      </MessageBubble>

      {/* Message actions */}
      <div className={clsx(
        'flex items-center mt-1 px-1',
        isUser ? 'justify-end' : 'justify-start ml-11'
      )}>
        <MessageActions
          message={message}
          onCopy={() => handleCopy()}
          onRegenerate={!isUser ? handleRegenerate : undefined}
          onFeedback={!isUser ? handleFeedback : undefined}
          onShare={handleShare}
        />
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
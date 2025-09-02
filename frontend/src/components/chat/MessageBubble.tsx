/**
 * MessageBubble component with enhanced styling and HSA bank branding.
 * 
 * Provides professional message display with distinct styling for user vs assistant messages,
 * including HSA bank branding colors, proper spacing, status indicators, and timestamps.
 */

import React from 'react';
import clsx from 'clsx';
import type { ChatMessage } from '@/types/hsaAssistant';

/**
 * Props for MessageBubble component.
 */
export interface MessageBubbleProps {
  /** The chat message to display */
  message: ChatMessage;
  /** Whether to show avatar */
  showAvatar?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Content to render inside the bubble */
  children?: React.ReactNode;
}

/**
 * HSA Assistant avatar component.
 */
const AssistantAvatar: React.FC<{ className?: string }> = ({ className }) => (
  <div className={clsx(
    'w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center flex-shrink-0',
    className
  )}>
    <svg
      className="w-5 h-5 text-white"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
      />
    </svg>
  </div>
);

/**
 * User avatar component.
 */
const UserAvatar: React.FC<{ className?: string }> = ({ className }) => (
  <div className={clsx(
    'w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center flex-shrink-0',
    className
  )}>
    <svg
      className="w-5 h-5 text-white"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
      />
    </svg>
  </div>
);

/**
 * Status indicator component.
 */
const StatusIndicator: React.FC<{ status?: ChatMessage['status'] }> = ({ status }) => {
  if (!status || status === 'success') return null;

  const getStatusConfig = () => {
    switch (status) {
      case 'sending':
        return {
          icon: (
            <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-primary-600" />
          ),
          text: 'Sending...',
          className: 'text-gray-500',
        };
      case 'error':
        return {
          icon: (
            <svg className="w-3 h-3 text-red-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          ),
          text: 'Failed to send',
          className: 'text-red-500',
        };
      default:
        return null;
    }
  };

  const config = getStatusConfig();
  if (!config) return null;

  return (
    <div className={clsx('flex items-center space-x-1 text-xs mt-1', config.className)}>
      {config.icon}
      <span>{config.text}</span>
    </div>
  );
};

/**
 * Time ago formatter.
 */
function formatTimeAgo(timestamp: string): string {
  const now = new Date();
  const messageTime = new Date(timestamp);
  const diffInSeconds = Math.floor((now.getTime() - messageTime.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return 'Just now';
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return `${minutes}m ago`;
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `${hours}h ago`;
  } else {
    const days = Math.floor(diffInSeconds / 86400);
    return `${days}d ago`;
  }
}

/**
 * MessageBubble component.
 */
export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  showAvatar = true,
  className,
  children,
}) => {
  const isUser = message.role === 'user';
  const isError = message.status === 'error';
  const isLoading = message.status === 'sending';

  return (
    <div
      className={clsx(
        'flex w-full mb-6 group',
        isUser ? 'justify-end' : 'justify-start',
        className
      )}
    >
      <div className={clsx(
        'flex max-w-[85%] space-x-3',
        isUser ? 'flex-row-reverse space-x-reverse' : 'flex-row'
      )}>
        {/* Avatar */}
        {showAvatar && (
          <div className="flex-shrink-0 mt-1">
            {isUser ? <UserAvatar /> : <AssistantAvatar />}
          </div>
        )}

        {/* Message content container */}
        <div className="flex flex-col min-w-0 flex-1">
          {/* Message bubble */}
          <div
            className={clsx(
              'rounded-2xl px-4 py-3 shadow-sm relative',
              // User message styling
              isUser && [
                'bg-primary-600 text-white',
                'rounded-br-md', // Sharp corner on bottom right
              ],
              // Assistant message styling
              !isUser && [
                isError
                  ? 'bg-red-50 border border-red-200 text-red-800'
                  : 'bg-white border border-gray-200 text-gray-900',
                'rounded-bl-md', // Sharp corner on bottom left
              ],
              // Loading state
              isLoading && 'opacity-75',
              // Hover effects
              'transition-all duration-200 ease-in-out',
              !isUser && 'group-hover:shadow-md',
            )}
          >
            {/* HSA Assistant label for first assistant message */}
            {!isUser && (
              <div className="text-xs font-semibold text-primary-600 mb-1">
                HSA Assistant
              </div>
            )}

            {/* Message content */}
            <div className={clsx(
              'break-words',
              isUser ? 'text-white' : isError ? 'text-red-800' : 'text-gray-900'
            )}>
              {children || message.content}
            </div>

            {/* Status indicator */}
            <StatusIndicator status={message.status} />

            {/* Confidence score for assistant messages */}
            {!isUser && message.confidence_score !== undefined && !isError && (
              <div className="mt-2 text-xs text-gray-500 flex items-center space-x-2">
                <div className="flex items-center">
                  <div
                    className={clsx(
                      'w-2 h-2 rounded-full mr-1',
                      message.confidence_score >= 0.8
                        ? 'bg-green-400'
                        : message.confidence_score >= 0.6
                        ? 'bg-yellow-400'
                        : 'bg-red-400'
                    )}
                  />
                  <span>
                    {(message.confidence_score * 100).toFixed(0)}% confident
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Timestamp */}
          <div className={clsx(
            'text-xs mt-1 px-1',
            isUser ? 'text-right text-gray-500' : 'text-left text-gray-500'
          )}>
            {formatTimeAgo(message.timestamp)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
/**
 * MessageActions component for interactive message functionality.
 * 
 * Provides copy, regenerate, feedback (thumbs up/down), and share actions
 * for chat messages with appropriate visibility based on message type and state.
 */

import React, { useState } from 'react';
import clsx from 'clsx';
import type { ChatMessage } from '@/types/hsaAssistant';

/**
 * Props for MessageActions component.
 */
export interface MessageActionsProps {
  /** The message these actions apply to */
  message: ChatMessage;
  /** Callback for copying message content */
  onCopy?: (content: string) => void;
  /** Callback for regenerating assistant response */
  onRegenerate?: (messageId: string) => void;
  /** Callback for feedback (thumbs up/down) */
  onFeedback?: (messageId: string, feedback: 'up' | 'down') => void;
  /** Callback for sharing message */
  onShare?: (messageId: string) => void;
  /** Whether actions are currently disabled */
  disabled?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Action button component.
 */
interface ActionButtonProps {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  disabled?: boolean;
  active?: boolean;
  variant?: 'default' | 'success' | 'danger';
  size?: 'sm' | 'md';
}

const ActionButton: React.FC<ActionButtonProps> = ({
  icon,
  label,
  onClick,
  disabled = false,
  active = false,
  variant = 'default',
  size = 'sm',
}) => {
  const getVariantClasses = () => {
    const base = 'transition-all duration-200 ease-in-out';
    
    switch (variant) {
      case 'success':
        return `${base} ${
          active 
            ? 'text-green-600 bg-green-50 hover:bg-green-100' 
            : 'text-gray-400 hover:text-green-600 hover:bg-green-50'
        }`;
      case 'danger':
        return `${base} ${
          active 
            ? 'text-red-600 bg-red-50 hover:bg-red-100' 
            : 'text-gray-400 hover:text-red-600 hover:bg-red-50'
        }`;
      default:
        return `${base} ${
          active 
            ? 'text-primary-600 bg-primary-50 hover:bg-primary-100' 
            : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
        }`;
    }
  };

  const getSizeClasses = () => {
    return size === 'md' ? 'p-2' : 'p-1.5';
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={label}
      className={clsx(
        'rounded-md border border-transparent',
        getSizeClasses(),
        getVariantClasses(),
        disabled && 'opacity-50 cursor-not-allowed',
        'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-opacity-50'
      )}
    >
      <span className="sr-only">{label}</span>
      {icon}
    </button>
  );
};

/**
 * Copy icon component.
 */
const CopyIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    className={clsx('w-4 h-4', className)}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
    />
  </svg>
);

/**
 * Regenerate icon component.
 */
const RegenerateIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    className={clsx('w-4 h-4', className)}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
    />
  </svg>
);

/**
 * Thumbs up icon component.
 */
const ThumbsUpIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    className={clsx('w-4 h-4', className)}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L9 7m-5 13h2.5a2 2 0 002-2V9a2 2 0 00-2-2H6a2 2 0 00-2 2v9a2 2 0 002 2z"
    />
  </svg>
);

/**
 * Thumbs down icon component.
 */
const ThumbsDownIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    className={clsx('w-4 h-4', className)}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018c.163 0 .326.02.485.06L17 4m-7 10v5a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L15 17m5-13H17.5a2 2 0 00-2 2v9a2 2 0 002 2H20a2 2 0 002-2V7a2 2 0 00-2-2z"
    />
  </svg>
);

/**
 * Share icon component.
 */
const ShareIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    className={clsx('w-4 h-4', className)}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z"
    />
  </svg>
);

/**
 * MessageActions component.
 */
export const MessageActions: React.FC<MessageActionsProps> = ({
  message,
  onCopy,
  onRegenerate,
  onFeedback,
  onShare,
  disabled = false,
  className,
}) => {
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);
  
  const isUser = message.role === 'user';
  const isError = message.status === 'error';
  const isLoading = message.status === 'sending';

  /**
   * Handle copy action.
   */
  const handleCopy = async () => {
    if (!onCopy || disabled) return;
    
    try {
      await navigator.clipboard.writeText(message.content);
      onCopy(message.content);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (error) {
      console.error('Failed to copy message:', error);
      // Fallback for browsers that don't support clipboard API
      onCopy(message.content);
    }
  };

  /**
   * Handle regenerate action.
   */
  const handleRegenerate = () => {
    if (!onRegenerate || disabled || isLoading) return;
    onRegenerate(message.id);
  };

  /**
   * Handle feedback action.
   */
  const handleFeedback = (type: 'up' | 'down') => {
    if (!onFeedback || disabled) return;
    
    const newFeedback = feedback === type ? null : type;
    setFeedback(newFeedback);
    
    if (newFeedback) {
      onFeedback(message.id, newFeedback);
    }
  };

  /**
   * Handle share action.
   */
  const handleShare = () => {
    if (!onShare || disabled) return;
    onShare(message.id);
  };

  // Don't show actions for loading messages
  if (isLoading) return null;

  return (
    <div className={clsx(
      'flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200',
      className
    )}>
      {/* Copy button */}
      <ActionButton
        icon={<CopyIcon />}
        label={copySuccess ? 'Copied!' : 'Copy message'}
        onClick={handleCopy}
        disabled={disabled}
        active={copySuccess}
        variant={copySuccess ? 'success' : 'default'}
      />

      {/* Regenerate button - only for assistant messages */}
      {!isUser && onRegenerate && (
        <ActionButton
          icon={<RegenerateIcon />}
          label="Regenerate response"
          onClick={handleRegenerate}
          disabled={disabled || isError}
        />
      )}

      {/* Feedback buttons - only for successful assistant messages */}
      {!isUser && !isError && onFeedback && (
        <>
          <ActionButton
            icon={<ThumbsUpIcon />}
            label="Good response"
            onClick={() => handleFeedback('up')}
            disabled={disabled}
            active={feedback === 'up'}
            variant="success"
          />
          <ActionButton
            icon={<ThumbsDownIcon />}
            label="Bad response"
            onClick={() => handleFeedback('down')}
            disabled={disabled}
            active={feedback === 'down'}
            variant="danger"
          />
        </>
      )}

      {/* Share button */}
      {onShare && (
        <ActionButton
          icon={<ShareIcon />}
          label="Share message"
          onClick={handleShare}
          disabled={disabled}
        />
      )}
    </div>
  );
};

export default MessageActions;
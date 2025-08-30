/**
 * ChatInput component for user message input.
 * 
 * Provides a text input area with send button, character limits,
 * keyboard shortcuts, and example questions for user guidance.
 */

import React, { useState, useRef, useEffect } from 'react';
import clsx from 'clsx';
import { Button } from '@/components/ui/Button';
import type { ChatInputProps } from '@/types/hsaAssistant';

/**
 * Example questions for user guidance.
 */
const EXAMPLE_QUESTIONS = [
  "What are the HSA contribution limits for 2024?",
  "Am I eligible for an HSA if I have other health insurance?",
  "Can I use my HSA for dental expenses?",
  "What happens to my HSA when I turn 65?",
];

/**
 * ChatInput component.
 */
export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  disabled = false,
  placeholder = "Ask me anything about HSA rules and eligibility...",
  className,
}) => {
  const [message, setMessage] = useState('');
  const [showExamples, setShowExamples] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const maxLength = 500;

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
    }
  }, [message]);

  // Focus input on mount
  useEffect(() => {
    if (textareaRef.current && !disabled) {
      textareaRef.current.focus();
    }
  }, [disabled]);

  /**
   * Handle form submission.
   */
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!message.trim() || disabled) return;
    
    onSendMessage(message.trim());
    setMessage('');
    setShowExamples(false);
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  /**
   * Handle keyboard shortcuts.
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
    
    if (e.key === 'Escape') {
      setShowExamples(false);
    }
  };

  /**
   * Handle example question selection.
   */
  const handleExampleClick = (question: string) => {
    setMessage(question);
    setShowExamples(false);
    textareaRef.current?.focus();
  };

  /**
   * Handle input focus.
   */
  const handleFocus = () => {
    if (!message.trim()) {
      setShowExamples(true);
    }
  };

  /**
   * Handle input blur.
   */
  const handleBlur = () => {
    // Delay hiding examples to allow clicking on them
    setTimeout(() => setShowExamples(false), 150);
  };

  const remainingChars = maxLength - message.length;
  const isNearLimit = remainingChars <= 50;
  const canSend = message.trim().length > 0 && !disabled;

  return (
    <div className={clsx('relative', className)}>
      {/* Example questions */}
      {showExamples && EXAMPLE_QUESTIONS.length > 0 && (
        <div className="absolute bottom-full left-0 right-0 mb-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto z-10">
          <div className="p-3 border-b border-gray-100">
            <div className="text-sm font-medium text-gray-700">
              Example questions:
            </div>
          </div>
          <div className="py-2">
            {EXAMPLE_QUESTIONS.map((question, index) => (
              <button
                key={index}
                onClick={() => handleExampleClick(question)}
                className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input form */}
      <form onSubmit={handleSubmit} className="flex flex-col space-y-2">
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={handleFocus}
            onBlur={handleBlur}
            placeholder={placeholder}
            disabled={disabled}
            maxLength={maxLength}
            rows={1}
            className={clsx(
              'w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg resize-none',
              'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
              'disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed',
              'placeholder-gray-400'
            )}
          />
          
          {/* Send button */}
          <div className="absolute right-2 bottom-2">
            <Button
              type="submit"
              size="sm"
              disabled={!canSend}
              className="rounded-full w-8 h-8 p-0 flex items-center justify-center"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
            </Button>
          </div>
        </div>

        {/* Character count and hints */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-2">
            {!disabled && (
              <span>Press Enter to send, Shift+Enter for new line</span>
            )}
          </div>
          <div className={clsx(
            isNearLimit && 'text-yellow-600 font-medium'
          )}>
            {remainingChars} characters remaining
          </div>
        </div>
      </form>
    </div>
  );
};

export default ChatInput;
/**
 * ChatCTA (Call-to-Action) component for HSA application engagement.
 * 
 * Displays a prominent call-to-action after meaningful chat engagement
 * to encourage users to start their HSA application process.
 */

import React from 'react';
import clsx from 'clsx';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import type { CTAProps } from '@/types/hsaAssistant';

/**
 * ChatCTA component.
 */
export const ChatCTA: React.FC<CTAProps> = ({
  show = false,
  title = "Ready to Open Your HSA?",
  description = "Based on our conversation, it looks like you might be eligible for an HSA. Start your application now to take advantage of the tax benefits and savings opportunities.",
  buttonText = "Start HSA Application",
  onStartApplication,
  className,
}) => {
  if (!show) return null;

  const handleStartApplication = () => {
    if (onStartApplication) {
      onStartApplication();
    } else {
      // Default behavior - could navigate to application page
      console.log('Starting HSA application...');
    }
  };

  return (
    <div
      className={clsx(
        'sticky bottom-4 mx-4 z-10 animate-fade-in-up',
        className
      )}
    >
      <Card className="bg-gradient-to-r from-primary-500 to-primary-600 text-white border-none shadow-lg">
        <div className="p-6">
          {/* Icon */}
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
            </div>

            <div className="flex-1 min-w-0">
              {/* Title */}
              <h3 className="text-lg font-semibold text-white mb-2">
                {title}
              </h3>

              {/* Description */}
              <p className="text-primary-100 text-sm leading-relaxed mb-4">
                {description}
              </p>

              {/* Benefits list */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
                <div className="flex items-center space-x-2">
                  <svg className="w-4 h-4 text-green-300" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm text-primary-100">Tax deductible</span>
                </div>
                <div className="flex items-center space-x-2">
                  <svg className="w-4 h-4 text-green-300" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm text-primary-100">Tax-free growth</span>
                </div>
                <div className="flex items-center space-x-2">
                  <svg className="w-4 h-4 text-green-300" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm text-primary-100">No expiration</span>
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex flex-col sm:flex-row gap-3">
                <Button
                  onClick={handleStartApplication}
                  variant="secondary"
                  className="bg-white text-primary-600 hover:bg-gray-50 border-none shadow-sm"
                >
                  {buttonText}
                </Button>
                <button className="text-sm text-primary-100 hover:text-white underline">
                  Continue chatting
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Subtle animation */}
        <div className="absolute inset-0 bg-gradient-to-r from-primary-400/10 to-transparent opacity-50 animate-pulse" />
      </Card>
    </div>
  );
};

/**
 * Hook to determine when to show CTA based on chat engagement.
 */
export function useCTAVisibility(messageCount: number, hasAskedAboutEligibility: boolean): boolean {
  // Show CTA after user has sent at least 3 messages and asked about eligibility
  return messageCount >= 6 || hasAskedAboutEligibility; // 6 = 3 user + 3 assistant messages
}

/**
 * Analyze messages to detect eligibility-related questions.
 */
export function hasEligibilityQuestions(messages: string[]): boolean {
  const eligibilityKeywords = [
    'eligible', 'eligibility', 'qualify', 'qualified', 'can i',
    'high deductible', 'hdhp', 'contribute', 'open', 'start'
  ];

  return messages.some(message =>
    eligibilityKeywords.some(keyword =>
      message.toLowerCase().includes(keyword.toLowerCase())
    )
  );
}

export default ChatCTA;
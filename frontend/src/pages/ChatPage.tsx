/**
 * ChatPage component - Main chat interface for HSA Assistant.
 * 
 * Integrates all chat components and provides the complete
 * conversational experience for HSA questions and guidance.
 */

import React, { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ChatProvider, useChat } from '@/contexts/ChatContext';
import { Layout } from '@/components/layout/Layout';
import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';
import { ChatCTA, useCTAVisibility, hasEligibilityQuestions } from '@/components/chat/ChatCTA';
import type { ChatPageProps } from '@/types/hsaAssistant';

/**
 * Inner chat page component that uses the chat context.
 */
const ChatPageInner: React.FC<ChatPageProps> = ({ applicationId: propApplicationId }) => {
  const navigate = useNavigate();
  const { applicationId: routeApplicationId } = useParams<{ applicationId?: string }>();
  const applicationId = propApplicationId || routeApplicationId;
  
  const {
    messages,
    isLoading,
    sendMessage,
    setApplicationId,
    loadHistory,
  } = useChat();

  // Set application ID if provided
  useEffect(() => {
    if (applicationId) {
      setApplicationId(applicationId);
    }
  }, [applicationId, setApplicationId]);

  // Load existing history on mount
  useEffect(() => {
    if (applicationId && applicationId !== 'new') {
      loadHistory(applicationId);
    }
  }, [applicationId, loadHistory]);

  // Determine CTA visibility based on engagement
  const userMessages = messages.filter(msg => msg.role === 'user').map(msg => msg.content);
  const messageCount = messages.length;
  const hasAskedAboutEligibility = hasEligibilityQuestions(userMessages);
  const showCTA = useCTAVisibility(messageCount, hasAskedAboutEligibility);

  /**
   * Handle starting HSA application.
   */
  const handleStartApplication = () => {
    // Navigate to personal info page to start application
    navigate('/personal-info');
  };

  /**
   * Handle sending message.
   */
  const handleSendMessage = async (message: string) => {
    await sendMessage(message);
  };

  return (
    <Layout>
      <div className="flex flex-col h-full max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex-shrink-0 border-b border-gray-200 bg-white px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">HSA Assistant</h1>
              <p className="text-sm text-gray-600 mt-1">
                Get answers to your Health Savings Account questions
              </p>
            </div>
            
            {/* Status indicator */}
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <span className="text-sm text-gray-500">Online</span>
            </div>
          </div>
        </div>

        {/* Chat content area */}
        <div className="flex-1 flex flex-col min-h-0 bg-gray-50">
          {/* Messages */}
          <MessageList
            messages={messages}
            isLoading={isLoading}
            className="flex-1"
          />

          {/* CTA overlay */}
          {showCTA && (
            <ChatCTA
              show={showCTA}
              onStartApplication={handleStartApplication}
            />
          )}

          {/* Input area */}
          <div className="flex-shrink-0 bg-white border-t border-gray-200 p-4">
            <ChatInput
              onSendMessage={handleSendMessage}
              disabled={isLoading}
              placeholder="Ask me anything about HSA rules, eligibility, or benefits..."
            />
          </div>
        </div>
      </div>
    </Layout>
  );
};

/**
 * Main ChatPage component with provider wrapper.
 */
export const ChatPage: React.FC<ChatPageProps> = ({ applicationId }) => {
  return (
    <ChatProvider initialApplicationId={applicationId}>
      <ChatPageInner applicationId={applicationId} />
    </ChatProvider>
  );
};

export default ChatPage;
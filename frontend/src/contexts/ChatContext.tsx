/**
 * Chat context provider for HSA Assistant state management.
 * 
 * Provides global state and actions for managing chat sessions,
 * including message history, loading states, and API interactions.
 */

import { createContext, useContext, useCallback, useReducer, ReactNode } from 'react';
import { hsaAssistantService } from '@/services/hsaAssistantService';
import type {
  ChatSession,
  ChatContextValue,
  ChatMessage,
  QAResponse,
  QAHistoryItem,
} from '@/types/hsaAssistant';

/**
 * Chat context actions for reducer.
 */
type ChatAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'ADD_USER_MESSAGE'; payload: ChatMessage }
  | { type: 'ADD_ASSISTANT_MESSAGE'; payload: ChatMessage }
  | { type: 'UPDATE_MESSAGE'; payload: { id: string; updates: Partial<ChatMessage> } }
  | { type: 'SET_MESSAGES'; payload: ChatMessage[] }
  | { type: 'CLEAR_MESSAGES' }
  | { type: 'SET_APPLICATION_ID'; payload: string | undefined };

/**
 * Initial chat session state.
 */
const initialState: ChatSession = {
  messages: [],
  isLoading: false,
  error: null,
  applicationId: undefined,
};

/**
 * Chat reducer for managing state updates.
 */
function chatReducer(state: ChatSession, action: ChatAction): ChatSession {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false };
    
    case 'ADD_USER_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload],
        error: null,
      };
    
    case 'ADD_ASSISTANT_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload],
        isLoading: false,
        error: null,
      };
    
    case 'UPDATE_MESSAGE':
      return {
        ...state,
        messages: state.messages.map(msg =>
          msg.id === action.payload.id
            ? { ...msg, ...action.payload.updates }
            : msg
        ),
      };
    
    case 'SET_MESSAGES':
      return { ...state, messages: action.payload };
    
    case 'CLEAR_MESSAGES':
      return { ...state, messages: [], error: null };
    
    case 'SET_APPLICATION_ID':
      return { ...state, applicationId: action.payload };
    
    default:
      return state;
  }
}

/**
 * Generate unique message ID.
 */
function generateMessageId(): string {
  return `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Convert QA history item to chat message.
 */
function historyItemToChatMessage(item: QAHistoryItem): ChatMessage[] {
  const userMessage: ChatMessage = {
    id: `${item.id}-user`,
    content: item.question,
    role: 'user',
    timestamp: item.created_at,
    status: 'success',
  };

  const assistantMessage: ChatMessage = {
    id: `${item.id}-assistant`,
    content: item.answer,
    role: 'assistant',
    timestamp: item.created_at,
    confidence_score: item.confidence_score,
    status: 'success',
  };

  return [userMessage, assistantMessage];
}

/**
 * Convert QA response to chat message.
 */
function responseToAssistantMessage(response: QAResponse): ChatMessage {
  return {
    id: generateMessageId(),
    content: response.answer,
    role: 'assistant',
    timestamp: response.created_at,
    citations: response.citations,
    confidence_score: response.confidence_score,
    status: 'success',
  };
}

/**
 * Chat context.
 */
const ChatContext = createContext<ChatContextValue | undefined>(undefined);

/**
 * Props for ChatProvider.
 */
interface ChatProviderProps {
  children: ReactNode;
  initialApplicationId?: string;
}

/**
 * Chat provider component.
 */
export function ChatProvider({ children, initialApplicationId }: ChatProviderProps) {
  const [state, dispatch] = useReducer(chatReducer, {
    ...initialState,
    applicationId: initialApplicationId,
  });

  /**
   * Send a new message to the assistant.
   */
  const sendMessage = useCallback(async (question: string): Promise<void> => {
    if (!question.trim()) return;

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: generateMessageId(),
      content: question.trim(),
      role: 'user',
      timestamp: new Date().toISOString(),
      status: 'success',
    };

    dispatch({ type: 'ADD_USER_MESSAGE', payload: userMessage });
    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      // Get context from recent messages for follow-up questions
      const recentMessages = state.messages.slice(-4); // Last 2 exchanges
      const context = recentMessages
        .filter(msg => msg.role === 'assistant')
        .map(msg => msg.content)
        .join(' ');

      // Send question to API
      const response = await hsaAssistantService.askQuestion(
        question.trim(),
        context || undefined,
        state.applicationId
      );

      // Add assistant response
      const assistantMessage = responseToAssistantMessage(response);
      dispatch({ type: 'ADD_ASSISTANT_MESSAGE', payload: assistantMessage });

    } catch (error) {
      console.error('Failed to send message:', error);
      
      // Add error message
      const errorMessage: ChatMessage = {
        id: generateMessageId(),
        content: 'Sorry, I encountered an error processing your question. Please try again.',
        role: 'assistant',
        timestamp: new Date().toISOString(),
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      };

      dispatch({ type: 'ADD_ASSISTANT_MESSAGE', payload: errorMessage });
      dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Unknown error occurred' });
    }
  }, [state.messages, state.applicationId]);

  /**
   * Clear all messages from the chat.
   */
  const clearMessages = useCallback((): void => {
    dispatch({ type: 'CLEAR_MESSAGES' });
  }, []);

  /**
   * Load chat history from backend.
   */
  const loadHistory = useCallback(async (applicationId?: string): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      const historyItems = await hsaAssistantService.getHistory(
        applicationId || state.applicationId || 'all'
      );

      // Convert history items to chat messages
      const messages: ChatMessage[] = [];
      historyItems.forEach(item => {
        messages.push(...historyItemToChatMessage(item));
      });

      dispatch({ type: 'SET_MESSAGES', payload: messages });
      
    } catch (error) {
      console.error('Failed to load history:', error);
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error instanceof Error ? error.message : 'Failed to load history' 
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [state.applicationId]);

  /**
   * Set application ID for the session.
   */
  const setApplicationId = useCallback((id: string): void => {
    dispatch({ type: 'SET_APPLICATION_ID', payload: id });
  }, []);

  /**
   * Retry a failed message.
   */
  const retryMessage = useCallback(async (messageId: string): Promise<void> => {
    const message = state.messages.find(msg => msg.id === messageId);
    if (!message || message.role !== 'user') return;

    // Update message status to sending
    dispatch({
      type: 'UPDATE_MESSAGE',
      payload: { id: messageId, updates: { status: 'sending' } }
    });

    await sendMessage(message.content);
  }, [state.messages, sendMessage]);

  /**
   * Copy message content to clipboard.
   */
  const copyMessage = useCallback(async (messageId: string): Promise<void> => {
    const message = state.messages.find(msg => msg.id === messageId);
    if (!message) return;

    try {
      await navigator.clipboard.writeText(message.content);
      
      // Update message to show it was copied
      dispatch({
        type: 'UPDATE_MESSAGE',
        payload: { id: messageId, updates: { copied: true } }
      });

      // Reset copied status after 2 seconds
      setTimeout(() => {
        dispatch({
          type: 'UPDATE_MESSAGE',
          payload: { id: messageId, updates: { copied: false } }
        });
      }, 2000);
    } catch (error) {
      console.error('Failed to copy message:', error);
    }
  }, [state.messages]);

  /**
   * Regenerate assistant response.
   */
  const regenerateResponse = useCallback(async (messageId: string): Promise<void> => {
    // Find the assistant message to regenerate
    const assistantMessageIndex = state.messages.findIndex(msg => msg.id === messageId);
    if (assistantMessageIndex === -1) return;

    const assistantMessage = state.messages[assistantMessageIndex];
    if (assistantMessage.role !== 'assistant') return;

    // Find the preceding user message
    const userMessage = assistantMessageIndex > 0 
      ? state.messages[assistantMessageIndex - 1]
      : null;

    if (!userMessage || userMessage.role !== 'user') return;

    // Remove the assistant message and regenerate
    const updatedMessages = state.messages.filter(msg => msg.id !== messageId);
    dispatch({ type: 'SET_MESSAGES', payload: updatedMessages });

    // Resend the user's question
    await sendMessage(userMessage.content);
  }, [state.messages, sendMessage]);

  /**
   * Provide feedback on a message.
   */
  const provideFeedback = useCallback(async (messageId: string, feedback: 'up' | 'down'): Promise<void> => {
    // Update message with feedback
    dispatch({
      type: 'UPDATE_MESSAGE',
      payload: { id: messageId, updates: { feedback } }
    });

    // In a real app, you might want to send this feedback to the backend
    // for analytics or training purposes
    console.log(`Feedback provided for message ${messageId}:`, feedback);
  }, []);

  /**
   * Share message.
   */
  const shareMessage = useCallback(async (messageId: string): Promise<void> => {
    const message = state.messages.find(msg => msg.id === messageId);
    if (!message) return;

    try {
      // Use Web Share API if available
      if (navigator.share) {
        await navigator.share({
          title: 'HSA Assistant Message',
          text: message.content,
        });
      } else {
        // Fallback to clipboard
        await navigator.clipboard.writeText(message.content);
        console.log('Message copied to clipboard for sharing');
      }
    } catch (error) {
      console.error('Failed to share message:', error);
    }
  }, [state.messages]);

  const contextValue: ChatContextValue = {
    ...state,
    sendMessage,
    clearMessages,
    loadHistory,
    setApplicationId,
    retryMessage,
    copyMessage,
    regenerateResponse,
    provideFeedback,
    shareMessage,
  };

  return (
    <ChatContext.Provider value={contextValue}>
      {children}
    </ChatContext.Provider>
  );
}

/**
 * Hook to use chat context.
 * 
 * @returns Chat context value
 * @throws Error if used outside of ChatProvider
 */
export function useChat(): ChatContextValue {
  const context = useContext(ChatContext);
  
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  
  return context;
}

/**
 * Default export for convenience.
 */
export default ChatProvider;
/**
 * TypeScript interfaces for HSA Assistant chat functionality.
 * 
 * Defines types for chat messages, API requests/responses, and UI state
 * management for the HSA Assistant chatbot system.
 */

/**
 * Citation reference from knowledge base.
 */
export interface Citation {
  /** Name of the source document */
  document_name: string;
  /** Page number within the document (if applicable) */
  page_number?: number;
  /** Relevant excerpt from the source document */
  excerpt: string;
  /** Relevance score for this citation (0.0 = not relevant, 1.0 = highly relevant) */
  relevance_score: number;
}

/**
 * Request schema for asking questions about HSA rules.
 */
export interface QARequest {
  /** The question about HSA rules and eligibility */
  question: string;
  /** Optional context for follow-up questions */
  context?: string;
  /** Application ID for tracking Q&A history */
  application_id?: string;
}

/**
 * Response schema for HSA Q&A answers.
 */
export interface QAResponse {
  /** AI-generated answer based on HSA knowledge base */
  answer: string;
  /** Confidence score for the answer quality (0.0 = low confidence, 1.0 = high confidence) */
  confidence_score: number;
  /** List of citations supporting the answer */
  citations: Citation[];
  /** List of source document names used */
  source_documents: string[];
  /** Time taken to process the question in milliseconds */
  processing_time_ms?: number;
  /** When the response was generated */
  created_at: string;
}

/**
 * Q&A session history item.
 */
export interface QAHistoryItem {
  /** Unique identifier for this Q&A interaction */
  id: string;
  /** The question that was asked */
  question: string;
  /** The answer that was provided */
  answer: string;
  /** Confidence score for the answer */
  confidence_score: number;
  /** Number of citations provided with the answer */
  citations_count: number;
  /** Associated application ID */
  application_id?: string;
  /** When the question was asked */
  created_at: string;
}

/**
 * Chat message type for UI display.
 */
export interface ChatMessage {
  /** Unique message identifier */
  id: string;
  /** Message content/text */
  content: string;
  /** Sender type */
  role: 'user' | 'assistant';
  /** Timestamp when message was created */
  timestamp: string;
  /** Citations for assistant messages */
  citations?: Citation[];
  /** Confidence score for assistant responses */
  confidence_score?: number;
  /** Processing status */
  status?: 'sending' | 'success' | 'error';
  /** Error message if status is error */
  error?: string;
}

/**
 * Chat session state for context provider.
 */
export interface ChatSession {
  /** Current list of messages in the chat */
  messages: ChatMessage[];
  /** Whether a request is currently being processed */
  isLoading: boolean;
  /** Any error that occurred during the session */
  error: string | null;
  /** Application ID associated with this session */
  applicationId?: string;
}

/**
 * Chat context actions for state management.
 */
export interface ChatContextActions {
  /** Send a new message */
  sendMessage: (question: string) => Promise<void>;
  /** Clear all messages */
  clearMessages: () => void;
  /** Load chat history from backend */
  loadHistory: (applicationId?: string) => Promise<void>;
  /** Set application ID for the session */
  setApplicationId: (id: string) => void;
  /** Retry failed message */
  retryMessage: (messageId: string) => Promise<void>;
}

/**
 * Complete chat context interface combining state and actions.
 */
export interface ChatContextValue extends ChatSession, ChatContextActions {}

/**
 * Props for chat components.
 */
export interface ChatComponentProps {
  /** Additional CSS classes */
  className?: string;
}

/**
 * Message list props.
 */
export interface MessageListProps extends ChatComponentProps {
  /** List of messages to display */
  messages: ChatMessage[];
  /** Whether messages are loading */
  isLoading?: boolean;
}

/**
 * Chat input props.
 */
export interface ChatInputProps extends ChatComponentProps {
  /** Callback when a message is sent */
  onSendMessage: (message: string) => void;
  /** Whether input is disabled (e.g., during loading) */
  disabled?: boolean;
  /** Placeholder text */
  placeholder?: string;
}

/**
 * Citation display props.
 */
export interface CitationProps {
  /** Citation to display */
  citation: Citation;
  /** Index in citation list */
  index: number;
}

/**
 * CTA (Call-to-Action) props.
 */
export interface CTAProps extends ChatComponentProps {
  /** Whether to show the CTA */
  show: boolean;
  /** Title text for the CTA */
  title?: string;
  /** Description text for the CTA */
  description?: string;
  /** Button text */
  buttonText?: string;
  /** Click handler for the CTA button */
  onStartApplication?: () => void;
}

/**
 * Chat page props.
 */
export interface ChatPageProps {
  /** Initial application ID if continuing existing session */
  applicationId?: string;
}
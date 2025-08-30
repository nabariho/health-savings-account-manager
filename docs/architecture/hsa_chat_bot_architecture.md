# HSA Chatbot Architecture - Retrieval-Augmented Generation (RAG) System

## Executive Summary

This document defines the technical architecture for the HSA FAQ chatbot system using Retrieval-Augmented Generation (RAG). The chatbot provides users with accurate, citation-backed answers to HSA-related questions while seamlessly integrating with the onboarding flow through strategically placed call-to-action buttons.

## Architecture Overview

### High-Level System Design

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   OpenAI APIs   │
│   Chat UI       │◄──►│   QA Service    │◄──►│   Assistants    │
│   React/TS      │    │   Python        │    │   Vector Stores │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────┐
         │     OpenAI Vector Store             │
         │  • File Upload & Processing         │
         │  • Automatic Chunking               │
         │  • Built-in Search                  │
         └─────────────────────────────────────┘
```

### Technology Stack

#### Core Components
- **AI Platform**: OpenAI Assistants API with built-in file search
- **Vector Store**: OpenAI Vector Stores (managed service)
- **Response Model**: `gpt-4o-mini-2024-07-18`
- **Document Processing**: Native OpenAI file processing
- **Backend Framework**: FastAPI with async/await patterns
- **Frontend Framework**: React 18 with TypeScript

## RAG Pipeline Architecture

### 1. Knowledge Base Construction

#### Document Ingestion with OpenAI Vector Stores

```python
class OpenAIKnowledgeBaseBuilder:
    """Handles document upload to OpenAI Vector Stores"""
    
    async def ingest_documents(self, document_paths: List[str]) -> str:
        """
        Upload HSA documents to OpenAI Vector Store
        
        Simplified Pipeline:
        1. Create/update vector store
        2. Upload PDF documents directly to OpenAI
        3. OpenAI handles chunking, embedding, and indexing automatically
        """
        # Create or retrieve vector store
        vector_store = await self.openai_client.beta.vector_stores.create(
            name="hsa_knowledge_base",
            expires_after={
                "anchor": "last_active_at",
                "days": 365
            }
        )
        
        # Upload documents
        file_ids = []
        for doc_path in document_paths:
            # Upload file to OpenAI
            with open(doc_path, 'rb') as file:
                uploaded_file = await self.openai_client.files.create(
                    file=file,
                    purpose="assistants"
                )
                file_ids.append(uploaded_file.id)
        
        # Add files to vector store
        await self.openai_client.beta.vector_stores.file_batches.create(
            vector_store_id=vector_store.id,
            file_ids=file_ids
        )
        
        return vector_store.id
```

#### Chunking Strategy (Handled by OpenAI)

```python
class OpenAIChunkingStrategy:
    """OpenAI Vector Stores handle chunking automatically"""
    
    def __init__(self):
        """
        OpenAI automatically handles:
        - Optimal chunk sizing for embeddings
        - Semantic boundary preservation
        - Overlap strategy for context
        - Document structure recognition
        
        No manual chunking required - OpenAI optimizes for:
        - text-embedding-3-large model
        - Maximum retrieval quality
        - Automatic metadata extraction
        """
        self.chunk_info = {
            "strategy": "automatic",
            "provider": "openai",
            "optimization": "retrieval_quality",
            "note": "Chunking handled by OpenAI Vector Stores"
        }
```

### 2. Query Processing with OpenAI Assistants

#### Simplified Question Processing

```python
class OpenAIQueryProcessor:
    """Handles user questions via OpenAI Assistants API"""
    
    async def process_query(self, question: str, context: str = None) -> RAGResponse:
        """
        Simplified RAG pipeline using OpenAI Assistants:
        1. Create thread for conversation
        2. Send message with question
        3. Run assistant with file search enabled
        4. Extract response and citations
        """
        # Create conversation thread
        thread = await self.openai_client.beta.threads.create()
        
        # Add user message
        await self.openai_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=question
        )
        
        # Run assistant with file search
        run = await self.openai_client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant_id,
            tools=[{"type": "file_search"}]
        )
        
        # Wait for completion and get response
        run = await self._wait_for_completion(run)
        messages = await self.openai_client.beta.threads.messages.list(
            thread_id=thread.id
        )
        
        # Extract response and citations
        return await self._extract_response_with_citations(messages)
```

#### Assistant Configuration

```python
class OpenAIAssistantManager:
    """Manages HSA Assistant configuration"""
    
    async def create_hsa_assistant(self, vector_store_id: str) -> str:
        """
        Create specialized HSA assistant with file search:
        - Connects to HSA knowledge base vector store
        - Optimized instructions for HSA domain
        - Built-in search and citation capabilities
        """
        assistant = await self.openai_client.beta.assistants.create(
            name="HSA Expert Assistant",
            instructions="""You are an expert HSA advisor with access to official IRS documentation.
            
            Guidelines:
            - Provide accurate HSA information based solely on the uploaded documents
            - Include specific citations from IRS publications
            - Use clear, accessible language for financial concepts
            - Acknowledge limitations when information is insufficient
            - Emphasize important deadlines and requirements
            - Always cite the specific document and section for your answers
            """,
            model="gpt-4o-mini-2024-07-18",
            tools=[{"type": "file_search"}],
            tool_resources={
                "file_search": {
                    "vector_store_ids": [vector_store_id]
                }
            }
        )
        
        return assistant.id
```

### 3. Response Generation with Built-in Citations

#### OpenAI Assistant Response Processing

```python
class OpenAIResponseProcessor:
    """Process responses from OpenAI Assistants with automatic citations"""
    
    async def extract_response_with_citations(
        self, 
        messages: List[Message]
    ) -> RAGResponse:
        """
        Extract response and citations from OpenAI Assistant:
        1. Get latest assistant message
        2. Extract text content and file citations
        3. Process citation annotations
        4. Calculate confidence based on citation quality
        """
        # Get the latest assistant message
        assistant_message = next(
            msg for msg in reversed(messages.data) 
            if msg.role == "assistant"
        )
        
        # Extract text content
        text_content = next(
            content for content in assistant_message.content
            if content.type == "text"
        )
        
        answer = text_content.text.value
        
        # Process citations from annotations
        citations = []
        if text_content.text.annotations:
            for annotation in text_content.text.annotations:
                if annotation.type == "file_citation":
                    citation = await self._process_file_citation(annotation)
                    citations.append(citation)
        
        # Calculate confidence based on citation quality
        confidence = self._calculate_confidence_from_citations(citations)
        
        # Extract unique source documents
        source_documents = list(set(
            citation.document_name for citation in citations
        ))
        
        return RAGResponse(
            answer=answer,
            confidence_score=confidence,
            citations=citations,
            source_documents=source_documents
        )
    
    async def _process_file_citation(self, annotation) -> Citation:
        """Convert OpenAI file citation to our Citation format"""
        file_citation = annotation.file_citation
        
        # Get file details
        file_details = await self.openai_client.files.retrieve(
            file_citation.file_id
        )
        
        return Citation(
            document_name=file_details.filename,
            page_number=None,  # OpenAI doesn't provide page numbers
            section=None,      # Extract from quote if available
            excerpt=file_citation.quote or "",
            confidence=0.9     # High confidence for OpenAI citations
        )
```

## REST API Specifications

### QA Service Endpoints

#### POST /api/v1/qa/query

**Purpose**: Process user questions and return contextualized answers

**Request Schema**:
```python
class QAQueryRequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=500, description="User's HSA question")
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")
    context: Optional[str] = Field(None, description="Additional context from user flow")
    stream: bool = Field(False, description="Enable streaming response")
```

**Response Schema**:
```python
class QAQueryResponse(BaseModel):
    answer: str = Field(..., description="Generated answer with context")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Answer confidence")
    citations: List[Citation] = Field(default_factory=list, description="Source citations")
    source_documents: List[str] = Field(default_factory=list, description="Referenced documents")
    session_id: str = Field(..., description="Session tracking ID")
    response_time_ms: int = Field(..., description="Processing time")
    
class Citation(BaseModel):
    document_name: str = Field(..., description="Source document filename")
    page_number: Optional[int] = Field(None, description="Page reference")
    section: Optional[str] = Field(None, description="Document section")
    excerpt: str = Field(..., max_length=200, description="Relevant text excerpt")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Citation relevance")
```

**Implementation**:
```python
@router.post("/query", response_model=QAQueryResponse)
async def process_qa_query(
    request: QAQueryRequest,
    assistant_service: OpenAIAssistantService = Depends(get_assistant_service),
    session_service: SessionService = Depends(get_session_service)
) -> QAQueryResponse:
    """Process user question with OpenAI Assistant"""
    
    # Track session for conversation context
    session_id = request.session_id or await session_service.create_session()
    
    # Process with OpenAI Assistant
    start_time = time.time()
    assistant_response = await assistant_service.ask_question(
        question=request.question,
        context=request.context,
        session_id=session_id
    )
    processing_time = int((time.time() - start_time) * 1000)
    
    # Log interaction for analytics
    await session_service.log_interaction(
        session_id=session_id,
        question=request.question,
        response=assistant_response,
        processing_time=processing_time
    )
    
    return QAQueryResponse(
        answer=assistant_response.answer,
        confidence_score=assistant_response.confidence_score,
        citations=assistant_response.citations,
        source_documents=assistant_response.source_documents,
        session_id=session_id,
        response_time_ms=processing_time
    )
```

#### POST /api/v1/qa/ingest

**Purpose**: Upload documents to OpenAI Vector Store (Admin only)

**Request Schema**:
```python
class IngestRequest(BaseModel):
    document_paths: List[str] = Field(..., description="Paths to documents to upload")
    force_rebuild: bool = Field(False, description="Force vector store recreation")
    # chunk_size removed - OpenAI handles chunking automatically
```

**Response Schema**:
```python
class IngestResponse(BaseModel):
    task_id: str = Field(..., description="Background task ID")
    status: str = Field(..., description="Initial status")
    estimated_duration: int = Field(..., description="Estimated completion time in seconds")
```

#### GET /api/v1/qa/ingest/{task_id}/status

**Purpose**: Check knowledge base rebuild status

**Response Schema**:
```python
class IngestStatusResponse(BaseModel):
    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    progress: float = Field(..., ge=0.0, le=1.0, description="Completion percentage")
    documents_processed: int = Field(..., description="Number of documents processed")
    total_documents: int = Field(..., description="Total documents to process")
    error_message: Optional[str] = Field(None, description="Error details if failed")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
```

## Frontend Architecture

### Chat Component System

#### Core Chat Interface

```typescript
interface ChatPageProps {
  onStartApplication: () => void;
}

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  citations?: Citation[];
  confidence?: number;
  isLoading?: boolean;
}

interface ChatState {
  messages: ChatMessage[];
  currentInput: string;
  isLoading: boolean;
  sessionId: string;
  error: string | null;
}

const ChatPage: React.FC<ChatPageProps> = ({ onStartApplication }) => {
  const [state, dispatch] = useReducer(chatReducer, initialChatState);
  const { submitQuestion, isLoading } = useChatService();
  
  const handleSubmitQuestion = async (question: string) => {
    try {
      dispatch({ type: 'ADD_USER_MESSAGE', payload: { content: question } });
      dispatch({ type: 'SET_LOADING', payload: true });
      
      const response = await submitQuestion({
        question,
        sessionId: state.sessionId
      });
      
      dispatch({ 
        type: 'ADD_ASSISTANT_MESSAGE', 
        payload: {
          content: response.answer,
          citations: response.citations,
          confidence: response.confidence_score
        }
      });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };
  
  return (
    <div className="chat-container">
      <ChatHeader />
      <MessageList messages={state.messages} />
      <ChatInput 
        onSubmit={handleSubmitQuestion}
        disabled={isLoading}
        placeholder="Ask me anything about HSAs..."
      />
      <CTASection onStartApplication={onStartApplication} />
    </div>
  );
};
```

#### Citation Display Component

```typescript
interface CitationProps {
  citations: Citation[];
  className?: string;
}

const CitationDisplay: React.FC<CitationProps> = ({ citations, className }) => {
  const [expandedCitation, setExpandedCitation] = useState<string | null>(null);
  
  if (!citations.length) return null;
  
  return (
    <div className={`citations-container ${className || ''}`}>
      <h4 className="citations-header">Sources:</h4>
      <div className="citations-list">
        {citations.map((citation, index) => (
          <CitationItem
            key={citation.id || index}
            citation={citation}
            index={index + 1}
            isExpanded={expandedCitation === citation.id}
            onToggle={() => setExpandedCitation(
              expandedCitation === citation.id ? null : citation.id
            )}
          />
        ))}
      </div>
    </div>
  );
};

const CitationItem: React.FC<{
  citation: Citation;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
}> = ({ citation, index, isExpanded, onToggle }) => (
  <div className="citation-item">
    <button 
      className="citation-button"
      onClick={onToggle}
      aria-expanded={isExpanded}
    >
      <span className="citation-number">[{index}]</span>
      <span className="citation-document">{citation.document_name}</span>
      {citation.page_number && (
        <span className="citation-page">Page {citation.page_number}</span>
      )}
    </button>
    
    {isExpanded && (
      <div className="citation-excerpt">
        <p>{citation.excerpt}</p>
        <div className="citation-metadata">
          {citation.section && (
            <span className="citation-section">Section: {citation.section}</span>
          )}
          <span className="citation-confidence">
            Relevance: {(citation.confidence * 100).toFixed(0)}%
          </span>
        </div>
      </div>
    )}
  </div>
);
```

#### Call-to-Action Integration

```typescript
interface CTASectionProps {
  onStartApplication: () => void;
  className?: string;
}

const CTASection: React.FC<CTASectionProps> = ({ onStartApplication, className }) => {
  const [showCTA, setShowCTA] = useState(false);
  const chatMessages = useChatContext();
  
  // Show CTA after meaningful interaction
  useEffect(() => {
    const hasValidResponses = chatMessages.some(
      msg => msg.type === 'assistant' && msg.confidence && msg.confidence > 0.7
    );
    setShowCTA(hasValidResponses && chatMessages.length >= 2);
  }, [chatMessages]);
  
  if (!showCTA) return null;
  
  return (
    <div className={`cta-section ${className || ''}`}>
      <div className="cta-content">
        <h3>Ready to open your HSA?</h3>
        <p>Get started with your application - it only takes a few minutes.</p>
        <Button
          variant="primary"
          size="large"
          onClick={onStartApplication}
          className="cta-button"
        >
          Start Your HSA Application
        </Button>
      </div>
    </div>
  );
};
```

### State Management

#### Chat Context Provider

```typescript
interface ChatContextValue {
  messages: ChatMessage[];
  sessionId: string;
  isLoading: boolean;
  error: string | null;
  submitQuestion: (question: string) => Promise<void>;
  clearHistory: () => void;
  exportHistory: () => void;
}

export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(chatReducer, initialState);
  const chatService = useChatService();
  
  const submitQuestion = useCallback(async (question: string) => {
    dispatch({ type: 'ADD_USER_MESSAGE', payload: { content: question } });
    dispatch({ type: 'SET_LOADING', payload: true });
    
    try {
      const response = await chatService.query({
        question,
        sessionId: state.sessionId
      });
      
      dispatch({
        type: 'ADD_ASSISTANT_MESSAGE',
        payload: {
          content: response.answer,
          citations: response.citations,
          confidence: response.confidence_score
        }
      });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [chatService, state.sessionId]);
  
  const value: ChatContextValue = {
    messages: state.messages,
    sessionId: state.sessionId,
    isLoading: state.isLoading,
    error: state.error,
    submitQuestion,
    clearHistory: () => dispatch({ type: 'CLEAR_HISTORY' }),
    exportHistory: () => {
      // Export chat history as JSON for support/debugging
      const blob = new Blob([JSON.stringify(state.messages, null, 2)], {
        type: 'application/json'
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `hsa-chat-${state.sessionId}.json`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };
  
  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
};
```

## Error Handling and Edge Cases

### Backend Error Handling

```python
class QAServiceError(Exception):
    """Base exception for QA service errors"""
    pass

class InsufficientContextError(QAServiceError):
    """Raised when retrieved context is insufficient for answering"""
    pass

class EmbeddingGenerationError(QAServiceError):
    """Raised when embedding generation fails"""
    pass

class VectorStoreError(QAServiceError):
    """Raised when vector store operations fail"""
    pass

@router.post("/query")
async def process_qa_query(request: QAQueryRequest) -> QAQueryResponse:
    try:
        response = await rag_service.answer_question(request.question)
        return response
    except InsufficientContextError:
        return QAQueryResponse(
            answer="I don't have enough information in my knowledge base to answer that question accurately. Please try rephrasing or asking about HSA eligibility, contribution limits, or qualified expenses.",
            confidence_score=0.0,
            citations=[],
            source_documents=[],
            session_id=request.session_id or str(uuid.uuid4()),
            response_time_ms=0
        )
    except EmbeddingGenerationError as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Temporary service unavailable. Please try again in a moment."
        )
    except Exception as e:
        logger.error(f"Unexpected QA service error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again."
        )
```

### Frontend Error Handling

```typescript
const useChatService = () => {
  const handleServiceError = (error: any): string => {
    if (error.response?.status === 503) {
      return "The service is temporarily unavailable. Please try again in a few moments.";
    }
    if (error.response?.status === 429) {
      return "Too many requests. Please wait a moment before asking another question.";
    }
    if (error.code === 'NETWORK_ERROR') {
      return "Network connection issue. Please check your internet connection and try again.";
    }
    return "Something went wrong. Please try asking your question differently.";
  };

  const submitQuestion = async (request: QAQueryRequest) => {
    try {
      const response = await apiClient.post('/qa/query', request);
      return response.data;
    } catch (error) {
      const message = handleServiceError(error);
      throw new Error(message);
    }
  };

  return { submitQuestion };
};
```

## Performance Considerations

### OpenAI Vector Store Optimization

```python
class OpenAIVectorStoreOptimization:
    """Optimization strategies for OpenAI Vector Stores"""
    
    def __init__(self):
        self.response_cache = LRUCache(maxsize=1000)
        self.vector_store_cache = {}
    
    async def optimized_search(self, question: str, assistant_id: str) -> RAGResponse:
        """Optimized search with response caching"""
        
        # Check response cache first
        cache_key = self._generate_cache_key(question)
        if cache_key in self.response_cache:
            return self.response_cache[cache_key]
        
        # Use OpenAI's optimized search
        response = await self._query_assistant(question, assistant_id)
        
        # Cache successful responses
        if response.confidence_score > 0.7:
            self.response_cache[cache_key] = response
        
        return response
    
    def _generate_cache_key(self, question: str) -> str:
        """Generate cache key for semantically similar questions"""
        # Normalize question for better cache hits
        normalized = question.lower().strip()
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    async def get_vector_store_status(self, vector_store_id: str) -> dict:
        """Monitor vector store performance metrics"""
        vector_store = await self.openai_client.beta.vector_stores.retrieve(
            vector_store_id
        )
        
        return {
            "status": vector_store.status,
            "file_counts": vector_store.file_counts,
            "usage_bytes": vector_store.usage_bytes,
            "last_active_at": vector_store.last_active_at,
            "expires_after": vector_store.expires_after
        }
```

### Response Caching with Redis

```python
class OpenAIResponseCache:
    """Intelligent caching for OpenAI Assistant responses"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.ttl = 3600 * 24  # 24 hour cache
    
    async def get_cached_response(self, question: str) -> Optional[QAQueryResponse]:
        """Get cached response using question similarity"""
        
        # Normalize question for cache lookup
        normalized_question = self._normalize_question(question)
        cache_key = f"qa_cache:{hashlib.md5(normalized_question.encode()).hexdigest()}"
        
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            cache_entry = json.loads(cached_data)
            # Check if cache entry is still valid
            if self._is_cache_valid(cache_entry):
                return QAQueryResponse.parse_raw(cache_entry['response'])
        
        return None
    
    async def cache_response(self, question: str, response: QAQueryResponse) -> None:
        """Cache high-quality responses"""
        # Only cache responses with good confidence
        if response.confidence_score < 0.6:
            return
        
        normalized_question = self._normalize_question(question)
        cache_key = f"qa_cache:{hashlib.md5(normalized_question.encode()).hexdigest()}"
        
        cache_entry = {
            'question': normalized_question,
            'response': response.json(),
            'cached_at': datetime.utcnow().isoformat(),
            'confidence': response.confidence_score
        }
        
        await self.redis.setex(cache_key, self.ttl, json.dumps(cache_entry))
    
    def _normalize_question(self, question: str) -> str:
        """Normalize question for better cache hits"""
        normalized = question.lower().strip()
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized
```

## Security and Privacy Considerations

### Input Sanitization

```python
class QuerySanitizer:
    """Sanitize user inputs for security and quality"""
    
    BLOCKED_PATTERNS = [
        r'(?i)(prompt|ignore|system|assistant)',  # Prompt injection attempts
        r'(?i)(sql|drop|delete|insert|update)',   # SQL injection patterns
        r'<script|javascript|onclick',            # XSS patterns
        r'(?i)(api.?key|secret|token|password)'   # Credential fishing
    ]
    
    def sanitize_question(self, question: str) -> str:
        """Clean and validate user questions"""
        
        # Basic sanitization
        question = question.strip()
        question = re.sub(r'[<>]', '', question)  # Remove HTML brackets
        
        # Check for blocked patterns
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, question):
                raise ValidationError("Question contains prohibited content")
        
        # Length validation
        if len(question) < 10:
            raise ValidationError("Question too short")
        if len(question) > 500:
            raise ValidationError("Question too long")
        
        return question
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/query")
@limiter.limit("10/minute")  # 10 questions per minute per IP
async def process_qa_query(
    request: Request,
    qa_request: QAQueryRequest
) -> QAQueryResponse:
    """Rate-limited QA endpoint"""
    pass
```

## Monitoring and Observability

### Performance Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Business metrics
QA_QUESTIONS_TOTAL = Counter('hsa_qa_questions_total', 'Total questions asked', ['confidence_bucket'])
QA_RESPONSE_TIME = Histogram('hsa_qa_response_time_seconds', 'QA response time')
QA_CONFIDENCE_SCORE = Histogram('hsa_qa_confidence_score', 'Answer confidence scores')

# Technical metrics  
EMBEDDING_GENERATION_TIME = Histogram('embedding_generation_seconds', 'Embedding generation time')
VECTOR_SEARCH_TIME = Histogram('vector_search_seconds', 'Vector search time')
KNOWLEDGE_BASE_SIZE = Gauge('knowledge_base_chunks_total', 'Total chunks in knowledge base')

@router.post("/query")
async def process_qa_query(request: QAQueryRequest) -> QAQueryResponse:
    with QA_RESPONSE_TIME.time():
        # Process request...
        response = await rag_service.answer_question(request.question)
        
        # Record metrics
        confidence_bucket = 'high' if response.confidence_score > 0.8 else 'medium' if response.confidence_score > 0.5 else 'low'
        QA_QUESTIONS_TOTAL.labels(confidence_bucket=confidence_bucket).inc()
        QA_CONFIDENCE_SCORE.observe(response.confidence_score)
        
        return response
```

### Logging Strategy

```python
import structlog

logger = structlog.get_logger()

class QAService:
    async def answer_question(self, question: str) -> RAGResponse:
        session_id = str(uuid.uuid4())
        
        logger.info(
            "Processing QA request",
            session_id=session_id,
            question_length=len(question),
            question_hash=hashlib.md5(question.encode()).hexdigest()[:8]
        )
        
        try:
            # Process question...
            response = await self._generate_response(question)
            
            logger.info(
                "QA request completed",
                session_id=session_id,
                confidence=response.confidence_score,
                citations_count=len(response.citations),
                response_length=len(response.answer)
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "QA request failed",
                session_id=session_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
```

## Integration Points

### Application State Integration

```typescript
// Integration with main application state
interface ApplicationState {
  currentStep: 'qa_session' | 'personal_info' | 'document_upload' | 'decision';
  personalInfo: PersonalInfoForm | null;
  documents: DocumentUpload[];
  qaSession: QASession;
  decision: ApplicationDecision | null;
}

interface QASession {
  sessionId: string;
  messages: ChatMessage[];
  hasEngaged: boolean;  // User asked meaningful questions
  confidenceMetrics: {
    averageConfidence: number;
    totalQuestions: number;
    highConfidenceResponses: number;
  };
}

// Context provider integration
const ApplicationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(applicationReducer, initialState);
  
  const handleChatCompletion = (qaSession: QASession) => {
    dispatch({
      type: 'UPDATE_QA_SESSION',
      payload: qaSession
    });
    
    // Automatically advance if user has engaged meaningfully
    if (qaSession.hasEngaged && qaSession.confidenceMetrics.averageConfidence > 0.7) {
      dispatch({ type: 'ADVANCE_TO_PERSONAL_INFO' });
    }
  };
  
  return (
    <ApplicationContext.Provider value={{ state, dispatch, handleChatCompletion }}>
      {children}
    </ApplicationContext.Provider>
  );
};
```

## Deployment Configuration

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_ORG_ID=org-...

# OpenAI Services
OPENAI_ASSISTANT_ID=asst_...
OPENAI_VECTOR_STORE_ID=vs_...

# Knowledge Base
KNOWLEDGE_BASE_PATH=/data/knowledge_base
AUTO_UPLOAD_DOCUMENTS=false

# Performance Tuning
QA_RESPONSE_CACHE_TTL=3600
QA_MAX_CONCURRENT_REQUESTS=10
QA_TIMEOUT_SECONDS=60  # OpenAI can take longer

# Redis Cache
REDIS_URL=redis://localhost:6379
REDIS_CACHE_PREFIX=hsa_qa

# Monitoring
PROMETHEUS_METRICS_PORT=9090
LOG_LEVEL=INFO
STRUCTURED_LOGGING=true
```

### Docker Configuration

```dockerfile
# Add to backend Dockerfile
COPY requirements-qa.txt .
RUN pip install --no-cache-dir -r requirements-qa.txt

# Create knowledge base directory for document uploads
RUN mkdir -p /data/knowledge_base
COPY data/knowledge_base/ /data/knowledge_base/

# Health check for QA service
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/qa/health')"

# Additional environment for OpenAI services
ENV OPENAI_API_TIMEOUT=60
ENV OPENAI_MAX_RETRIES=3
```

This architecture provides a robust, scalable foundation for the HSA chatbot system with clear separation of concerns, comprehensive error handling, and production-ready deployment considerations.
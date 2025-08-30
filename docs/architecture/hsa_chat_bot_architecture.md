# HSA Chatbot Architecture - Retrieval-Augmented Generation (RAG) System

## Executive Summary

This document defines the technical architecture for the HSA FAQ chatbot system using Retrieval-Augmented Generation (RAG). The chatbot provides users with accurate, citation-backed answers to HSA-related questions while seamlessly integrating with the onboarding flow through strategically placed call-to-action buttons.

## Architecture Overview

### High-Level System Design

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   OpenAI APIs   │
│   Chat UI       │◄──►│   QA Service    │◄──►│   GPT-4o-mini   │
│   React/TS      │    │   Python        │    │   Embeddings    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┬─────────────────┬─────────────────┐
│  Vector Store   │  Document       │  Citation       │
│  FAISS/SQLite   │  Processor      │  Handler        │
└─────────────────┴─────────────────┴─────────────────┘
```

### Technology Stack

#### Core Components
- **Embedding Model**: `text-embedding-3-large` (1,536 dimensions)
- **Response Model**: `gpt-4o-mini-2024-07-18`
- **Vector Store**: FAISS for prototype, SQLite with pgvector for production
- **Document Processing**: PDF text extraction with chunk optimization
- **Backend Framework**: FastAPI with async/await patterns
- **Frontend Framework**: React 18 with TypeScript

## RAG Pipeline Architecture

### 1. Knowledge Base Construction

#### Document Ingestion Pipeline

```python
class KnowledgeBaseBuilder:
    """Handles ingestion and vectorization of HSA documentation"""
    
    async def ingest_documents(self, document_paths: List[str]) -> None:
        """
        Process HSA documents into searchable vector embeddings
        
        Pipeline:
        1. Extract text from PDF documents
        2. Split into optimized chunks (512-1024 tokens)
        3. Generate embeddings using text-embedding-3-large
        4. Store in vector database with metadata
        """
        for doc_path in document_paths:
            # Extract text preserving structure
            document = await self._extract_pdf_text(doc_path)
            
            # Intelligent chunking with overlap
            chunks = await self._create_smart_chunks(
                text=document.text,
                chunk_size=1024,
                overlap=128,
                preserve_structure=True
            )
            
            # Generate embeddings for each chunk
            for chunk in chunks:
                embedding = await self.openai_client.embeddings.create(
                    model="text-embedding-3-large",
                    input=chunk.text,
                    encoding_format="float"
                )
                
                # Store with rich metadata
                await self.vector_store.store(
                    id=chunk.id,
                    embedding=embedding.data[0].embedding,
                    metadata={
                        "document": doc_path,
                        "page_number": chunk.page,
                        "section": chunk.section,
                        "text": chunk.text,
                        "tokens": chunk.token_count,
                        "created_at": datetime.utcnow()
                    }
                )
```

#### Chunking Strategy

```python
class SmartChunker:
    """Intelligent document chunking preserving semantic boundaries"""
    
    def create_chunks(self, text: str, chunk_size: int = 1024) -> List[TextChunk]:
        """
        Create chunks optimized for HSA content:
        - Preserve section headers and numbered lists
        - Maintain sentence boundaries
        - Include contextual overlap
        - Optimize for embedding model token limits
        """
        # Preserve HSA-specific structure
        sections = self._identify_hsa_sections(text)
        chunks = []
        
        for section in sections:
            # Split long sections while preserving context
            section_chunks = self._split_section_preserving_context(
                section, chunk_size
            )
            chunks.extend(section_chunks)
        
        return chunks
```

### 2. Query Processing Pipeline

#### Question Analysis and Embedding

```python
class QueryProcessor:
    """Handles user questions and retrieval logic"""
    
    async def process_query(self, question: str, context: str = None) -> RAGResponse:
        """
        Full RAG pipeline for question answering:
        1. Preprocess and validate user question
        2. Generate query embedding
        3. Retrieve relevant document chunks
        4. Generate contextualized response
        5. Extract citations and confidence scores
        """
        # Preprocess question
        processed_question = await self._preprocess_question(question)
        
        # Generate embedding for similarity search
        question_embedding = await self.openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=processed_question,
            encoding_format="float"
        )
        
        # Retrieve relevant chunks
        relevant_chunks = await self._retrieve_relevant_chunks(
            embedding=question_embedding.data[0].embedding,
            k=5,
            similarity_threshold=0.75
        )
        
        # Generate response with citations
        return await self._generate_response(processed_question, relevant_chunks)
```

#### Similarity Search and Retrieval

```python
class VectorStore:
    """Vector similarity search with FAISS backend"""
    
    async def similarity_search(
        self, 
        query_embedding: List[float], 
        k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[RetrievedChunk]:
        """
        Efficient similarity search with filtering:
        - Cosine similarity with FAISS index
        - Threshold-based filtering
        - Diversity ranking to avoid redundant results
        - Metadata-enriched results
        """
        # Perform vector similarity search
        similarities, indices = self.faiss_index.search(
            np.array([query_embedding]), k * 2  # Over-retrieve for diversity
        )
        
        # Filter by threshold and diversify
        filtered_results = []
        for similarity, idx in zip(similarities[0], indices[0]):
            if similarity >= similarity_threshold:
                chunk = await self._get_chunk_by_index(idx)
                filtered_results.append(RetrievedChunk(
                    chunk=chunk,
                    similarity=similarity,
                    rank=len(filtered_results)
                ))
        
        # Apply diversity ranking
        diverse_results = self._apply_diversity_ranking(filtered_results, k)
        return diverse_results
```

### 3. Response Generation

#### Context Preparation and Prompt Engineering

```python
class ResponseGenerator:
    """Generate contextually accurate responses with citations"""
    
    async def generate_response(
        self, 
        question: str, 
        retrieved_chunks: List[RetrievedChunk]
    ) -> RAGResponse:
        """
        Generate response using retrieved context:
        1. Prepare context from retrieved chunks
        2. Engineer prompt for HSA domain
        3. Generate response with GPT-4o-mini
        4. Extract citations and confidence metrics
        """
        if not retrieved_chunks:
            return self._generate_no_answer_response()
        
        # Prepare context with proper attribution
        context = self._prepare_context(retrieved_chunks)
        
        # HSA-specific prompt engineering
        system_prompt = """
        You are an expert HSA advisor providing accurate information based solely on official IRS documentation.
        
        Guidelines:
        - Answer only based on the provided context
        - Include specific citations to document sections
        - If information is insufficient, acknowledge limitations
        - Use clear, accessible language for financial concepts
        - Emphasize important deadlines and requirements
        """
        
        user_prompt = f"""
        Based on the following HSA documentation context, answer this question: {question}
        
        Context:
        {context}
        
        Please provide a clear, accurate answer with citations to the specific document sections used.
        If the context doesn't contain sufficient information, clearly state this limitation.
        """
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for consistency
            max_tokens=1000
        )
        
        # Extract citations and calculate confidence
        citations = self._extract_citations(retrieved_chunks)
        confidence = self._calculate_confidence(retrieved_chunks, response)
        
        return RAGResponse(
            answer=response.choices[0].message.content,
            confidence_score=confidence,
            citations=citations,
            source_documents=list(set(chunk.metadata['document'] for chunk in retrieved_chunks))
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
    rag_service: RAGService = Depends(get_rag_service),
    session_service: SessionService = Depends(get_session_service)
) -> QAQueryResponse:
    """Process user question with RAG pipeline"""
    
    # Track session for conversation context
    session_id = request.session_id or await session_service.create_session()
    
    # Process with RAG pipeline
    start_time = time.time()
    rag_response = await rag_service.answer_question(
        question=request.question,
        context=request.context,
        session_id=session_id
    )
    processing_time = int((time.time() - start_time) * 1000)
    
    # Log interaction for analytics
    await session_service.log_interaction(
        session_id=session_id,
        question=request.question,
        response=rag_response,
        processing_time=processing_time
    )
    
    return QAQueryResponse(
        answer=rag_response.answer,
        confidence_score=rag_response.confidence_score,
        citations=rag_response.citations,
        source_documents=rag_response.source_documents,
        session_id=session_id,
        response_time_ms=processing_time
    )
```

#### POST /api/v1/qa/ingest

**Purpose**: Rebuild knowledge base from updated documents (Admin only)

**Request Schema**:
```python
class IngestRequest(BaseModel):
    document_paths: List[str] = Field(..., description="Paths to documents to ingest")
    force_rebuild: bool = Field(False, description="Force complete rebuild")
    chunk_size: int = Field(1024, ge=256, le=2048, description="Chunk size for processing")
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

### Vector Store Optimization

```python
class OptimizedVectorStore:
    """High-performance vector store with caching and indexing"""
    
    def __init__(self):
        self.faiss_index = self._build_optimized_index()
        self.cache = LRUCache(maxsize=1000)
        self.index_metadata = {}
    
    def _build_optimized_index(self) -> faiss.Index:
        """Build FAISS index optimized for HSA content"""
        # Use IVF (Inverted File) with PQ (Product Quantization) for large datasets
        quantizer = faiss.IndexFlatL2(1536)  # text-embedding-3-large dimension
        index = faiss.IndexIVFPQ(quantizer, 1536, 100, 8, 8)  # 100 clusters, 8-bit PQ
        
        # Train index if needed
        if self._needs_training():
            training_data = self._get_training_embeddings()
            index.train(training_data)
        
        return index
    
    async def similarity_search_optimized(
        self,
        query_embedding: np.ndarray,
        k: int = 5
    ) -> List[RetrievedChunk]:
        """Optimized search with caching and pre-filtering"""
        
        # Check cache first
        cache_key = hashlib.md5(query_embedding.tobytes()).hexdigest()
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Perform search with optimized parameters
        self.faiss_index.nprobe = 20  # Search 20 clusters
        similarities, indices = self.faiss_index.search(query_embedding, k * 2)
        
        # Post-process and cache results
        results = await self._process_search_results(similarities[0], indices[0], k)
        self.cache[cache_key] = results
        
        return results
```

### Response Caching Strategy

```python
class ResponseCache:
    """Intelligent caching for common HSA questions"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.ttl = 3600 * 24  # 24 hour cache
    
    async def get_cached_response(self, question: str) -> Optional[QAQueryResponse]:
        """Get cached response for semantically similar questions"""
        
        # Generate embedding for question
        question_embedding = await self._embed_question(question)
        
        # Check for semantically similar cached questions
        similar_questions = await self._find_similar_cached_questions(question_embedding)
        
        if similar_questions:
            # Return highest similarity cached response
            best_match = max(similar_questions, key=lambda x: x['similarity'])
            if best_match['similarity'] > 0.95:  # Very high similarity threshold
                return QAQueryResponse.parse_raw(best_match['response'])
        
        return None
    
    async def cache_response(self, question: str, response: QAQueryResponse) -> None:
        """Cache response with semantic indexing"""
        question_embedding = await self._embed_question(question)
        
        cache_entry = {
            'question': question,
            'embedding': question_embedding.tolist(),
            'response': response.json(),
            'cached_at': datetime.utcnow().isoformat()
        }
        
        await self.redis.setex(
            f"qa_cache:{hashlib.md5(question.encode()).hexdigest()}",
            self.ttl,
            json.dumps(cache_entry)
        )
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

# Vector Store Configuration
VECTOR_STORE_TYPE=faiss  # or 'sqlite' for production
FAISS_INDEX_PATH=/data/faiss_index
SQLITE_DB_URL=postgresql://user:pass@localhost:5432/hsa_db

# Knowledge Base
KNOWLEDGE_BASE_PATH=/data/knowledge_base
AUTO_REBUILD_KB=false
KB_CHUNK_SIZE=1024
KB_CHUNK_OVERLAP=128

# Performance Tuning
QA_RESPONSE_CACHE_TTL=3600
QA_MAX_CONCURRENT_REQUESTS=10
QA_TIMEOUT_SECONDS=30

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

# Install FAISS CPU version
RUN pip install faiss-cpu

# Create knowledge base directory
RUN mkdir -p /data/knowledge_base /data/faiss_index
COPY data/knowledge_base/ /data/knowledge_base/

# Health check for QA service
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/qa/health')"
```

This architecture provides a robust, scalable foundation for the HSA chatbot system with clear separation of concerns, comprehensive error handling, and production-ready deployment considerations.
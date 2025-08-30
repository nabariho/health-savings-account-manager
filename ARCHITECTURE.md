# HSA Onboarding System - Technical Architecture

## Executive Summary

This document defines the technical architecture for the AI-powered Health Savings Account (HSA) onboarding system. The solution implements a microservices-based approach using React/TypeScript frontend, Python backend with OpenAI Agents SDK, and specialized services for OCR/Vision processing, RAG-powered Q&A, and automated decisioning.

## Architecture Principles

### SOLID Principles
- **Single Responsibility**: Each service has one clearly defined purpose
- **Open/Closed**: Services are open for extension via configuration, closed for modification
- **Liskov Substitution**: All service implementations follow common interfaces
- **Interface Segregation**: Clean, minimal contracts between services
- **Dependency Inversion**: Services depend on abstractions, not concrete implementations

### KISS Methodology
- Prefer simple, testable solutions over complex abstractions
- Use established patterns and libraries where appropriate
- Avoid premature optimization and over-engineering
- Clear, readable code with explicit intentions

## System Overview

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   OpenAI APIs   │
│   React/TS      │◄──►│   Python        │◄──►│   GPT-4o        │
│   Tailwind      │    │   FastAPI       │    │   Embeddings    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│  Data Service   │  OCR Service    │  QA Service     │ Decision Engine │
│  SQLite/Files   │  Vision/Extract │  OpenAI Assist  │  Rules/Scoring  │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

## Frontend Architecture

### Technology Stack
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS 3.x
- **State Management**: React Context + useReducer for global state
- **HTTP Client**: Axios with interceptors for error handling
- **Form Management**: React Hook Form with Zod validation
- **File Upload**: React Dropzone with progress indicators
- **UI Components**: Headless UI + custom Tailwind components

### Module Structure
```
src/
├── components/           # Reusable UI components
│   ├── forms/           # Form-specific components
│   ├── layout/          # Layout components
│   ├── ui/              # Basic UI elements
│   └── upload/          # File upload components
├── hooks/               # Custom React hooks
├── pages/               # Page components
├── services/            # API service layer
├── stores/              # Context providers and state
├── types/               # TypeScript interfaces
├── utils/               # Utility functions
└── constants/           # Application constants
```

### Component Architecture

#### Data Collection Flow
```typescript
interface PersonalInfoForm {
  fullName: string;
  dateOfBirth: string;
  address: AddressInfo;
  socialSecurityNumber: string;
  employerName: string;
}

interface AddressInfo {
  street: string;
  city: string;
  state: string;
  zipCode: string;
}
```

#### Document Upload Flow
```typescript
interface DocumentUpload {
  type: 'government_id' | 'employer_document';
  file: File;
  status: 'pending' | 'processing' | 'completed' | 'error';
  extractedData?: ExtractedDocumentData;
}

interface ExtractedDocumentData {
  governmentId?: GovernmentIdData;
  employerDocument?: EmployerDocumentData;
}
```

#### Application State Management
```typescript
interface ApplicationState {
  currentStep: 'personal_info' | 'document_upload' | 'qa_session' | 'decision';
  personalInfo: PersonalInfoForm | null;
  documents: DocumentUpload[];
  qaSession: QAMessage[];
  decision: ApplicationDecision | null;
  errors: ApplicationError[];
}
```

## Backend Architecture

### Technology Stack
- **Framework**: FastAPI with Python 3.11+
- **ASGI Server**: Uvicorn for development, Gunicorn + Uvicorn workers for production
- **Database**: SQLite for prototype, PostgreSQL for production
- **ORM**: SQLAlchemy 2.0 with Alembic migrations
- **OpenAI Integration**: OpenAI Agents SDK + Responses API
- **Background Tasks**: Celery with Redis for async processing
- **Configuration**: Pydantic Settings for environment-based config

### Service Layer Architecture

#### Core Services

```python
# Service interfaces following dependency inversion
class DocumentProcessorInterface(ABC):
    @abstractmethod
    async def extract_government_id(self, file_data: bytes) -> GovernmentIdData:
        pass
    
    @abstractmethod
    async def extract_employer_document(self, file_data: bytes) -> EmployerDocumentData:
        pass

class RAGServiceInterface(ABC):
    @abstractmethod
    async def answer_question(self, question: str) -> RAGResponse:
        pass
    
    @abstractmethod
    async def build_knowledge_base(self, documents: List[str]) -> None:
        pass

class DecisionEngineInterface(ABC):
    @abstractmethod
    async def evaluate_application(self, application: ApplicationData) -> DecisionResult:
        pass
```

### Module Structure
```
backend/
├── api/                 # FastAPI routes and endpoints
│   ├── v1/             # API version 1
│   │   ├── auth/       # Authentication endpoints
│   │   ├── applications/ # Application CRUD
│   │   ├── documents/  # Document upload/processing
│   │   ├── qa/         # Q&A endpoints
│   │   └── decisions/  # Decision endpoints
├── core/               # Core business logic
│   ├── config.py       # Configuration management
│   ├── database.py     # Database setup and connection
│   ├── security.py     # Security utilities
│   └── dependencies.py # FastAPI dependencies
├── models/             # SQLAlchemy models
├── schemas/            # Pydantic schemas/DTOs
├── services/           # Business logic services
│   ├── document_processor.py
│   ├── rag_service.py
│   ├── decision_engine.py
│   └── audit_service.py
├── agents/             # OpenAI Agents configurations
├── utils/              # Utility functions
└── tests/              # Test suites
```

## Data Transfer Objects (DTOs)

### Request/Response Schemas

```python
# Personal Information DTO
class PersonalInfoRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: date = Field(...)
    address: AddressInfo = Field(...)
    social_security_number: str = Field(..., regex=r'^\d{3}-\d{2}-\d{4}$')
    employer_name: str = Field(..., min_length=2, max_length=100)

class AddressInfo(BaseModel):
    street: str = Field(..., min_length=5, max_length=200)
    city: str = Field(..., min_length=2, max_length=50)
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str = Field(..., regex=r'^\d{5}(-\d{4})?$')

# Document Processing DTOs
class DocumentUploadRequest(BaseModel):
    document_type: DocumentType = Field(...)
    file_name: str = Field(..., max_length=255)
    content_type: str = Field(...)

class GovernmentIdData(BaseModel):
    document_type: str = Field(...)
    id_number: str = Field(...)
    full_name: str = Field(...)
    date_of_birth: date = Field(...)
    address: AddressInfo = Field(...)
    issue_date: date = Field(...)
    expiry_date: date = Field(...)
    issuing_authority: str = Field(...)

class EmployerDocumentData(BaseModel):
    document_type: str = Field(...)
    employee_name: str = Field(...)
    employer_name: str = Field(...)
    employer_address: AddressInfo | None = Field(default=None)
    document_date: date = Field(...)
    health_plan_type: str | None = Field(default=None)

# RAG Service DTOs
class QARequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=500)
    context: str | None = Field(default=None)

class RAGResponse(BaseModel):
    answer: str = Field(...)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    citations: List[Citation] = Field(default_factory=list)
    source_documents: List[str] = Field(default_factory=list)

class Citation(BaseModel):
    document_name: str = Field(...)
    page_number: int | None = Field(default=None)
    excerpt: str = Field(..., max_length=200)

# Decision Engine DTOs
class DecisionRequest(BaseModel):
    application_id: str = Field(...)
    personal_info: PersonalInfoRequest = Field(...)
    extracted_government_id: GovernmentIdData = Field(...)
    extracted_employer_doc: EmployerDocumentData = Field(...)

class DecisionResult(BaseModel):
    application_id: str = Field(...)
    decision: DecisionType = Field(...)
    risk_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(...)
    validation_results: List[ValidationResult] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ValidationResult(BaseModel):
    field_name: str = Field(...)
    validation_type: ValidationType = Field(...)
    is_valid: bool = Field(...)
    confidence: float = Field(..., ge=0.0, le=1.0)
    details: str | None = Field(default=None)

# Enums
class DocumentType(str, Enum):
    GOVERNMENT_ID = "government_id"
    EMPLOYER_DOCUMENT = "employer_document"

class DecisionType(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    MANUAL_REVIEW = "manual_review"

class ValidationType(str, Enum):
    NAME_MATCH = "name_match"
    DOB_MATCH = "dob_match"
    ADDRESS_MATCH = "address_match"
    ID_EXPIRY = "id_expiry"
    DOCUMENT_QUALITY = "document_quality"
```

## REST API Contracts

### Application Management
```
POST /api/v1/applications
- Create new application
- Request: PersonalInfoRequest
- Response: ApplicationResponse

GET /api/v1/applications/{application_id}
- Retrieve application status
- Response: ApplicationResponse

PUT /api/v1/applications/{application_id}
- Update application information
- Request: PersonalInfoRequest
- Response: ApplicationResponse
```

### Document Processing
```
POST /api/v1/applications/{application_id}/documents
- Upload and process document
- Request: multipart/form-data with file + DocumentUploadRequest
- Response: DocumentProcessingResponse

GET /api/v1/applications/{application_id}/documents
- List all documents for application
- Response: List[DocumentResponse]

GET /api/v1/documents/{document_id}/status
- Check processing status
- Response: DocumentStatusResponse
```

### Q&A System
```
POST /api/v1/qa/query
- Process user questions with OpenAI Assistant
- Request: QAQueryRequest
- Response: QAQueryResponse

POST /api/v1/qa/ingest
- Upload documents to OpenAI Vector Store (Admin only)
- Request: IngestRequest
- Response: IngestResponse

GET /api/v1/qa/ingest/{task_id}/status
- Check document upload status
- Response: IngestStatusResponse

GET /api/v1/qa/history/{application_id}
- Get Q&A history for application
- Response: List[QAHistoryItem]
```

### Decision Management
```
POST /api/v1/applications/{application_id}/evaluate
- Trigger application evaluation
- Response: DecisionResult

GET /api/v1/applications/{application_id}/decision
- Get current decision status
- Response: DecisionResult

GET /api/v1/decisions/audit/{application_id}
- Get detailed audit trail
- Response: AuditTrail
```

## Specialized Services

### OCR/Vision Service (OpenAI GPT-4o Integration)

```python
class DocumentProcessor:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        self.vision_model = "gpt-4o"
    
    async def extract_government_id(self, image_data: bytes) -> GovernmentIdData:
        """
        Extract structured data from government ID using GPT-4o vision
        
        Args:
            image_data: Binary image data
            
        Returns:
            Structured government ID data
            
        Raises:
            DocumentProcessingError: If extraction fails
        """
        prompt = """
        Extract the following information from this government ID:
        - Document type (driver's license, passport, etc.)
        - ID number
        - Full name
        - Date of birth
        - Address (street, city, state, zip)
        - Issue date
        - Expiry date
        - Issuing authority
        
        Return as JSON with confidence scores for each field.
        """
        
        response = await self.openai_client.chat.completions.create(
            model=self.vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(image_data).decode()}"}}
                    ]
                }
            ],
            response_format={"type": "json_object"}
        )
        
        extracted_data = json.loads(response.choices[0].message.content)
        return GovernmentIdData.model_validate(extracted_data)
```

### QA Service (OpenAI Assistants API)

```python
class OpenAIQAService:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        self.assistant_id = None  # Set during initialization
        self.vector_store_id = None  # Set during initialization
    
    async def initialize_assistant(self, documents: List[str]) -> None:
        """
        Create OpenAI Assistant with Vector Store
        
        Args:
            documents: List of document paths to upload
        """
        # Create vector store
        vector_store = await self.openai_client.beta.vector_stores.create(
            name="hsa_knowledge_base",
            expires_after={
                "anchor": "last_active_at",
                "days": 365
            }
        )
        self.vector_store_id = vector_store.id
        
        # Upload documents
        file_ids = []
        for doc_path in documents:
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
        
        # Create assistant
        assistant = await self.openai_client.beta.assistants.create(
            name="HSA Expert Assistant",
            instructions="""You are an expert HSA advisor with access to official IRS documentation.
            
            Guidelines:
            - Provide accurate HSA information based solely on the uploaded documents
            - Include specific citations from IRS publications
            - Use clear, accessible language for financial concepts
            - Acknowledge limitations when information is insufficient
            - Always cite the specific document and section for your answers
            """,
            model="gpt-4o-mini-2024-07-18",
            tools=[{"type": "file_search"}],
            tool_resources={
                "file_search": {
                    "vector_store_ids": [vector_store.id]
                }
            }
        )
        self.assistant_id = assistant.id
    
    async def answer_question(self, question: str, session_id: str = None) -> RAGResponse:
        """
        Answer question using OpenAI Assistant with file search
        
        Args:
            question: User question
            session_id: Optional session ID for conversation tracking
            
        Returns:
            Response with answer and citations
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
        
        # Wait for completion
        while run.status in ['queued', 'in_progress']:
            await asyncio.sleep(1)
            run = await self.openai_client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
        
        if run.status != 'completed':
            return RAGResponse(
                answer="I'm sorry, I encountered an error processing your question. Please try again.",
                confidence_score=0.0,
                citations=[],
                source_documents=[]
            )
        
        # Get messages
        messages = await self.openai_client.beta.threads.messages.list(
            thread_id=thread.id
        )
        
        # Extract response and citations
        return await self._extract_response_with_citations(messages)
    
    async def _extract_response_with_citations(self, messages) -> RAGResponse:
        """Extract response and citations from OpenAI Assistant messages"""
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
        confidence = 0.9 if citations else 0.5
        
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
            for chunk in relevant_chunks
        ]
        
        return RAGResponse(
            answer=response.choices[0].message.content,
            confidence_score=self._calculate_confidence(relevant_chunks),
            citations=citations,
            source_documents=list(set([chunk.metadata['document'] for chunk in relevant_chunks]))
        )
```

### Decision Engine

```python
class DecisionEngine:
    def __init__(self, config: DecisionConfig):
        self.config = config
        self.rules = self._load_decision_rules()
    
    async def evaluate_application(self, application_data: ApplicationData) -> DecisionResult:
        """
        Evaluate application using business rules and risk scoring
        
        Args:
            application_data: Complete application data
            
        Returns:
            Decision result with reasoning
        """
        validation_results = []
        risk_factors = []
        
        # Rule 1: Check ID expiry
        if application_data.extracted_government_id.expiry_date < date.today():
            validation_results.append(
                ValidationResult(
                    field_name="id_expiry",
                    validation_type=ValidationType.ID_EXPIRY,
                    is_valid=False,
                    confidence=1.0,
                    details="Government ID is expired"
                )
            )
            risk_factors.append(("expired_id", 1.0))
        
        # Rule 2: Name matching
        name_match_score = self._fuzzy_match(
            application_data.personal_info.full_name,
            application_data.extracted_government_id.full_name
        )
        
        validation_results.append(
            ValidationResult(
                field_name="full_name",
                validation_type=ValidationType.NAME_MATCH,
                is_valid=name_match_score >= self.config.name_match_threshold,
                confidence=name_match_score,
                details=f"Name match confidence: {name_match_score:.2f}"
            )
        )
        
        if name_match_score < self.config.name_match_threshold:
            risk_factors.append(("name_mismatch", 1.0 - name_match_score))
        
        # Rule 3: Date of birth matching
        dob_match = (application_data.personal_info.date_of_birth == 
                    application_data.extracted_government_id.date_of_birth)
        
        validation_results.append(
            ValidationResult(
                field_name="date_of_birth",
                validation_type=ValidationType.DOB_MATCH,
                is_valid=dob_match,
                confidence=1.0 if dob_match else 0.0,
                details="Date of birth exact match" if dob_match else "Date of birth mismatch"
            )
        )
        
        if not dob_match:
            risk_factors.append(("dob_mismatch", 1.0))
        
        # Calculate final risk score
        risk_score = self._calculate_risk_score(risk_factors)
        
        # Make decision
        decision = self._make_decision(validation_results, risk_score)
        reasoning = self._generate_reasoning(validation_results, risk_factors)
        
        return DecisionResult(
            application_id=application_data.application_id,
            decision=decision,
            risk_score=risk_score,
            reasoning=reasoning,
            validation_results=validation_results
        )
    
    def _make_decision(self, validations: List[ValidationResult], risk_score: float) -> DecisionType:
        """Apply decision logic based on validation results and risk score"""
        
        # Auto-reject conditions
        if any(v.validation_type == ValidationType.ID_EXPIRY and not v.is_valid for v in validations):
            return DecisionType.REJECT
        
        # Manual review conditions
        if risk_score >= self.config.manual_review_threshold:
            return DecisionType.MANUAL_REVIEW
        
        if any(not v.is_valid for v in validations):
            return DecisionType.MANUAL_REVIEW
        
        # Auto-approve conditions
        if risk_score <= self.config.auto_approve_threshold:
            return DecisionType.APPROVE
        
        # Default to manual review for edge cases
        return DecisionType.MANUAL_REVIEW
```

### Audit Service

```python
class AuditService:
    def __init__(self, db: Database):
        self.db = db
    
    async def log_decision(self, decision_result: DecisionResult, 
                          application_data: ApplicationData) -> None:
        """
        Log decision with full audit trail
        
        Args:
            decision_result: The decision made
            application_data: Complete application data
        """
        audit_entry = AuditEntry(
            application_id=decision_result.application_id,
            decision=decision_result.decision,
            risk_score=decision_result.risk_score,
            reasoning=decision_result.reasoning,
            validation_results=decision_result.validation_results,
            application_snapshot=application_data.model_dump(),
            timestamp=datetime.utcnow(),
            system_version=self._get_system_version()
        )
        
        await self.db.audit_entries.create(audit_entry)
    
    async def get_audit_trail(self, application_id: str) -> AuditTrail:
        """Get complete audit trail for application"""
        entries = await self.db.audit_entries.get_by_application_id(application_id)
        return AuditTrail(
            application_id=application_id,
            entries=entries,
            created_at=min(e.timestamp for e in entries),
            updated_at=max(e.timestamp for e in entries)
        )
```

## Database Schema Design

### Core Tables

```sql
-- Applications table
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    full_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    address_street VARCHAR(200) NOT NULL,
    address_city VARCHAR(50) NOT NULL,
    address_state CHAR(2) NOT NULL,
    address_zip VARCHAR(10) NOT NULL,
    social_security_number VARCHAR(11) NOT NULL,
    employer_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id),
    document_type VARCHAR(20) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    processing_status VARCHAR(20) DEFAULT 'pending',
    extracted_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Decisions table
CREATE TABLE decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id),
    decision VARCHAR(20) NOT NULL,
    risk_score DECIMAL(5,4) NOT NULL,
    reasoning TEXT NOT NULL,
    validation_results JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- QA Sessions table
CREATE TABLE qa_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    confidence_score DECIMAL(5,4) NOT NULL,
    citations JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit Trail table
CREATE TABLE audit_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id),
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL,
    system_version VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge Base Embeddings table
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_name VARCHAR(255) NOT NULL,
    page_number INTEGER,
    text_content TEXT NOT NULL,
    embedding vector(1536), -- for text-embedding-3-large
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_created_at ON applications(created_at);
CREATE INDEX idx_documents_application_id ON documents(application_id);
CREATE INDEX idx_decisions_application_id ON decisions(application_id);
CREATE INDEX idx_qa_sessions_application_id ON qa_sessions(application_id);
CREATE INDEX idx_audit_entries_application_id ON audit_entries(application_id);
CREATE INDEX idx_knowledge_base_embedding ON knowledge_base USING ivfflat (embedding vector_cosine_ops);
```

## Data Flow Diagrams

### Application Processing Flow

```
User Input (Frontend)
      │
      ▼
┌─────────────────┐
│ Personal Info   │
│ Collection      │
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ Document Upload │
│ & Processing    │
└─────────────────┘
      │
      ▼
┌─────────────────┐    ┌─────────────────┐
│ OCR/Vision      │◄──►│ OpenAI GPT-4o   │
│ Extraction      │    │ API             │
└─────────────────┘    └─────────────────┘
      │
      ▼
┌─────────────────┐
│ Data Validation │
│ & Comparison    │
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ Decision Engine │
│ Risk Assessment │
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ Audit Logging   │
│ & Persistence   │
└─────────────────┘
      │
      ▼
Result to Frontend
```

### RAG Q&A Flow

```
User Question (Frontend)
      │
      ▼
┌─────────────────┐
│ Question        │
│ Preprocessing   │
└─────────────────┘
      │
      ▼
┌─────────────────┐    ┌─────────────────┐
│ Question        │◄──►│ OpenAI          │
│ Embedding       │    │ Embeddings API  │
└─────────────────┘    └─────────────────┘
      │
      ▼
┌─────────────────┐
│ Vector Search   │
│ Knowledge Base  │
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ Context         │
│ Preparation     │
└─────────────────┘
      │
      ▼
┌─────────────────┐    ┌─────────────────┐
│ Answer          │◄──►│ OpenAI          │
│ Generation      │    │ Responses API   │
└─────────────────┘    └─────────────────┘
      │
      ▼
┌─────────────────┐
│ Citation        │
│ Extraction      │
└─────────────────┘
      │
      ▼
Response to Frontend
```

## Security Considerations

### Authentication & Authorization
- JWT-based authentication for API access
- Role-based access control (applicant, reviewer, admin)
- API rate limiting to prevent abuse
- CORS configuration for frontend access

### Data Security
- Encryption at rest for sensitive data
- TLS 1.3 for all API communications
- Secure file upload validation and virus scanning
- PII data masking in logs and audit trails

### Input Validation
- Comprehensive input sanitization using Pydantic
- File type and size validation for uploads
- SQL injection prevention via ORM
- XSS protection in frontend components

### Secrets Management
- Environment variables for all secrets (OPENAI_API_KEY, DB_PASSWORD)
- No secrets in source code or git history
- Secrets rotation support via configuration

## Observability & Monitoring

### Application Performance Monitoring (APM)

```python
# Structured logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/application.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file']
    }
}
```

### Metrics Collection

```python
# Prometheus metrics for monitoring
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Business metrics
APPLICATIONS_TOTAL = Counter('applications_total', 'Total applications', ['status'])
DOCUMENT_PROCESSING_DURATION = Histogram('document_processing_duration_seconds', 'Document processing time')
DECISION_CONFIDENCE = Histogram('decision_confidence_score', 'Decision confidence scores')

# System metrics
OPENAI_API_CALLS = Counter('openai_api_calls_total', 'OpenAI API calls', ['model', 'endpoint'])
OPENAI_API_ERRORS = Counter('openai_api_errors_total', 'OpenAI API errors', ['model', 'error_type'])
```

### Health Checks

```python
# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/health/detailed")
async def detailed_health_check(db: Database = Depends(get_database)):
    """Detailed health check with dependencies"""
    checks = {
        "database": await _check_database(db),
        "openai_api": await _check_openai_api(),
        "vector_store": await _check_vector_store(),
        "file_storage": await _check_file_storage()
    }
    
    overall_status = "healthy" if all(c["status"] == "healthy" for c in checks.values()) else "unhealthy"
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.utcnow()
    }
```

### Error Tracking

```python
# Sentry integration for error tracking
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration(auto_enable=True)],
    traces_sample_rate=0.1,
    environment=os.getenv("ENVIRONMENT", "development")
)

# Custom exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.error(f"Validation error: {exc.errors()}", extra={
        "request_id": request.headers.get("X-Request-ID"),
        "path": request.url.path,
        "method": request.method
    })
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "error_type": "validation_error"}
    )
```

## Project Folder Structure

```
health-savings-account-manager/
├── README.md
├── ARCHITECTURE.md
├── PROJECT_ROADMAP.md
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── frontend/                    # React TypeScript Frontend
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── forms/
│   │   │   │   ├── PersonalInfoForm.tsx
│   │   │   │   └── DocumentUploadForm.tsx
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   └── Layout.tsx
│   │   │   ├── ui/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   └── Modal.tsx
│   │   │   └── upload/
│   │   │       ├── FileUploader.tsx
│   │   │       └── DocumentPreview.tsx
│   │   ├── hooks/
│   │   │   ├── useApplication.ts
│   │   │   ├── useDocumentUpload.ts
│   │   │   └── useQASession.ts
│   │   ├── pages/
│   │   │   ├── HomePage.tsx
│   │   │   ├── PersonalInfoPage.tsx
│   │   │   ├── DocumentUploadPage.tsx
│   │   │   ├── QAPage.tsx
│   │   │   └── DecisionPage.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── applicationService.ts
│   │   │   ├── documentService.ts
│   │   │   └── qaService.ts
│   │   ├── stores/
│   │   │   ├── ApplicationContext.tsx
│   │   │   └── ApplicationReducer.ts
│   │   ├── types/
│   │   │   ├── application.ts
│   │   │   ├── document.ts
│   │   │   └── api.ts
│   │   ├── utils/
│   │   │   ├── validation.ts
│   │   │   ├── formatting.ts
│   │   │   └── constants.ts
│   │   └── constants/
│   │       └── index.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   └── Dockerfile
│
├── backend/                     # Python FastAPI Backend
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── applications.py
│   │       ├── documents.py
│   │       ├── qa.py
│   │       └── decisions.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── dependencies.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── application.py
│   │   ├── document.py
│   │   ├── decision.py
│   │   └── audit.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── application.py
│   │   ├── document.py
│   │   ├── qa.py
│   │   └── decision.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_processor.py
│   │   ├── rag_service.py
│   │   ├── decision_engine.py
│   │   └── audit_service.py
│   ├── agents/                  # OpenAI Agents Configuration
│   │   ├── __init__.py
│   │   ├── document_agent.py
│   │   ├── qa_agent.py
│   │   └── decision_agent.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_handler.py
│   │   ├── validation.py
│   │   └── vector_store.py
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── alembic/                 # Database migrations
│   ├── logs/
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── main.py
│   └── Dockerfile
│
├── data/                        # Knowledge base and samples
│   ├── knowledge_base/
│   │   ├── HSA_FAQ.txt
│   │   └── HSA_Limits.txt
│   └── samples/
│       ├── sample_id.jpg
│       ├── sample_employer_doc.pdf
│       └── test_scenarios.json
│
├── docs/                        # Additional documentation
│   ├── architecture/
│   │   └── hsa_chat_bot_architecture.md  # Detailed RAG chatbot system design
│   ├── api/
│   │   └── openapi.yaml
│   ├── deployment/
│   │   └── kubernetes.yaml
│   └── wireframes/
│       └── ui_flow.png
│
├── scripts/                     # Utility scripts
│   ├── setup_dev.sh
│   ├── build_images.sh
│   └── run_tests.sh
│
└── monitoring/                  # Monitoring configuration
    ├── prometheus.yml
    ├── grafana/
    │   └── dashboards/
    └── alerting/
        └── rules.yml
```

## Docker Containerization Plan

### Multi-Stage Dockerfile for Backend

```dockerfile
# Backend Dockerfile
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Set work directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . .

# Create logs directory
RUN mkdir -p logs && chown -R appuser:appuser logs

# Switch to non-root user
USER appuser

# Add local Python packages to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Expose port
EXPOSE 8000

# Start command
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:8000", "--worker-class", "uvicorn.workers.UvicornWorker", "--workers", "4"]
```

### Multi-Stage Dockerfile for Frontend

```dockerfile
# Frontend Dockerfile
FROM node:18-alpine as builder

# Set work directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Create non-root user
RUN addgroup -g 1001 -S appuser && \
    adduser -S appuser -u 1001 -G appuser

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Change ownership of nginx directories
RUN chown -R appuser:appuser /usr/share/nginx/html && \
    chown -R appuser:appuser /var/cache/nginx && \
    chown -R appuser:appuser /var/log/nginx && \
    chown -R appuser:appuser /etc/nginx/conf.d

RUN touch /var/run/nginx.pid && \
    chown -R appuser:appuser /var/run/nginx.pid

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/ || exit 1

# Expose port
EXPOSE 8080

# Start command
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:8080"
    environment:
      - REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
    depends_on:
      - backend
    networks:
      - hsa-network
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://hsa_user:${DB_PASSWORD}@database:5432/hsa_db
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=development
    depends_on:
      - database
      - redis
    volumes:
      - ./backend/logs:/app/logs
      - ./data:/app/data:ro
    networks:
      - hsa-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3

  database:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=hsa_db
      - POSTGRES_USER=hsa_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - hsa-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hsa_user -d hsa_db"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - hsa-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Development tools (optional)
  pgadmin:
    image: dpage/pgadmin4:latest
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@hsa.local
      - PGADMIN_DEFAULT_PASSWORD=${PGADMIN_PASSWORD}
    ports:
      - "8080:80"
    depends_on:
      - database
    networks:
      - hsa-network
    profiles:
      - dev
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  hsa-network:
    driver: bridge
```

### Production Docker Compose Override

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  frontend:
    environment:
      - REACT_APP_API_BASE_URL=https://api.hsa.yourdomain.com/api/v1
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`hsa.yourdomain.com`)"
      - "traefik.http.routers.frontend.tls=true"
      - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"

  backend:
    environment:
      - DATABASE_URL=postgresql://hsa_user:${DB_PASSWORD}@database:5432/hsa_db
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=production
      - SENTRY_DSN=${SENTRY_DSN}
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.backend.rule=Host(`api.hsa.yourdomain.com`)"
      - "traefik.http.routers.backend.tls=true"
      - "traefik.http.routers.backend.tls.certresolver=letsencrypt"

  traefik:
    image: traefik:v2.10
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik/acme.json:/acme.json
    networks:
      - hsa-network
    restart: unless-stopped
```

This comprehensive architecture provides a robust foundation for building the HSA onboarding system with all the required features, proper separation of concerns, and production-ready deployment capabilities.
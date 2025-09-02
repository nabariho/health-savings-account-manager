# HSA Onboarding Project – User Stories

This document breaks down the work required to deliver the full HSA onboarding experience into small, self-contained user stories.  
Each story includes **prerequisites**, **requirements**, and **expected outputs** so Claude subagents can execute them with minimal ambiguity.  
The stories build on the architecture defined in `ARCHITECTURE.md` and the existing codebase.

---

## 1. Design a chatbot architecture for HSA FAQs  **Status:** COMPLETED

**Prerequisites**
- IRS HSA PDF exists at `data/knowledge_base/hsa/irs.pdf`.
- `ARCHITECTURE.md` exists with the base system (React/TS frontend, FastAPI backend).

**Requirements**
1. Define a Retrieval-Augmented Generation (RAG) pipeline:
    - Ingest IRS PDF into a knowledge base (embeddings with `text-embedding-3-large`).
    - Retrieve passages and call OpenAI Responses API (`gpt-4o-mini`) with context.
2. Specify endpoints:
    - `POST /qa/query` → answer questions with citations.
    - (Optional) `POST /qa/ingest` → rebuild knowledge base.
3. Decide on vector store/database (FAISS or SQLite for prototype).
4. Define frontend modules:
    - Chat component, citation rendering, CTA button.
5. Handle errors, rate limits, and no-answer cases.

**Expected Output**
- `/docs/architecture/hsa_chat_bot_architecture.md` documenting the system.
- Updates to `ARCHITECTURE.md`.
- Roadmap entry describing design decisions.

---

## 2. Implement backend HSA Assistant service (RAG) **Status:** DONE

**Prerequisites**
- Chatbot architecture document from Story 1.
- IRS PDF available for ingestion.

**Requirements**
- Create FastAPI router `backend/api/v1/qa.py`:
    - `POST /qa/query` → accept question, return streamed answer with citations.
    - `POST /qa/ingest` → rebuild embeddings.
- Implement `rag_service.py` with `build_knowledge_base()` and `answer_question()`.
- Use FAISS or lightweight DB for embeddings.
- Add tests verifying answers include citations and unknown questions fail gracefully.

**Expected Output**
- Functional QA endpoints.
- RAG service integrated.
- Passing tests for citation handling and fallbacks.

---

## 3. Implement chatbot UI and CTA **Status:** DONE

**Prerequisites**
- Backend QA service is available.

**Requirements**
- Add `ChatPage` component:
    - Chat history, user input, streaming answers with citations.
    - “Start Your HSA Application” CTA below chat.
- Update routing: CTA → personal info page.
- Update global state to include `qaSession`.
- Ensure accessibility, loading/error states.
- Add unit & integration tests.

**Expected Output**
- Functional chat interface with CTA.
- Navigation from chat → enrollment.
- Updated roadmap.

---

## 4. Enhanced Message Display with Rich Formatting **Status:** DONE **Priority:** P0

**Prerequisites**
- Existing ChatPage and MessageList components from Story 3.
- HSA Assistant API returning basic text responses.

**Requirements**
1. **Enhanced Message Bubbles**:
   - Distinct styling for user vs assistant messages with proper spacing
   - Rich text formatting support (bold, italics, bullet points, numbered lists)
   - Collapsible citation sections with source references
   - Message timestamp display with "time ago" format
   - Copy message functionality with toast notifications

2. **Professional HSA Sales Representative Styling**:
   - Assistant messages should display with bank branding colors
   - Professional avatar/icon for the HSA sales representative
   - Status indicators (typing, processing, delivered)
   - Structured response formatting with clear sections

3. **Message Actions**:
   - Copy button for each message
   - Regenerate response option for assistant messages  
   - Thumbs up/down feedback buttons
   - Share message functionality

**Expected Output**
- Enhanced MessageList component with rich formatting
- Updated MessageBubble subcomponent with professional styling
- Copy and feedback functionality implemented
- Collapsible citation display working
- Professional HSA sales representative visual identity

---

## 5. Professional Sales Representative Persona and Behavior **Status:** TODO **Priority:** P0

**Prerequisites**
- Enhanced message display from Story 4.
- HSA Assistant API integration working.

**Requirements**
1. **Sales Representative Persona**:
   - All responses should be from "Sarah, your HSA specialist"
   - Professional, helpful, and knowledgeable tone
   - Always reference IRS documentation when providing HSA information
   - Proactive suggestions for HSA optimization and tax benefits

2. **Enhanced Response Intelligence**:
   - Structured responses with clear headings and bullet points
   - Include relevant IRS document citations with confidence scores
   - Provide personalized HSA contribution recommendations
   - Offer follow-up questions to continue the conversation

3. **Lead Qualification Integration**:
   - Detect when users ask about HSA eligibility or setup
   - Naturally guide conversations toward account opening
   - Capture user intent and qualification status
   - Integrate with existing CTA flow seamlessly

**Expected Output**
- Updated HSA Assistant API responses with sales persona
- Professional conversation flow with lead qualification
- Enhanced response structure with IRS citations
- Integrated CTA triggering based on conversation context
- Updated chat context to track sales engagement

---

## 6. Chat Session Management and History **Status:** TODO **Priority:** P0

**Prerequisites**
- Enhanced message display from Story 4.
- Professional sales persona from Story 5.

**Requirements**
1. **Chat Session Management**:
   - Create new chat sessions with descriptive titles
   - Save and restore chat history across browser sessions
   - Session list with timestamps and preview messages
   - Delete individual sessions or clear all history

2. **ChatGPT-like Sidebar**:
   - Collapsible sidebar showing chat history
   - Search functionality across all chat sessions
   - Filter sessions by date, topic, or interaction type
   - Quick access to frequently asked HSA questions

3. **Enhanced Navigation**:
   - Today/Yesterday/This Week session grouping
   - Session renaming capability
   - Star/bookmark important conversations
   - Export conversation as PDF or text

**Expected Output**
- Chat sidebar component with session management
- Backend API for session CRUD operations
- Local storage integration for session persistence
- Search functionality across chat history
- Export functionality for conversations

---

## 7. Contextual Sales CTAs and Intelligent Engagement **Status:** TODO **Priority:** P1

**Prerequisites**
- Chat session management from Story 6.
- Sales representative persona from Story 5.

**Requirements**
1. **Intelligent CTA Timing**:
   - Analyze conversation context to determine optimal CTA placement
   - Show different CTAs based on user questions (eligibility, contributions, tax benefits)
   - Track user engagement and adjust CTA strategy
   - A/B test different CTA messages and timing

2. **Dynamic Sales Content**:
   - Display relevant HSA benefits based on conversation topics
   - Show personalized contribution calculators
   - Provide tax savings estimates based on user's situation
   - Include trust indicators (FDIC insurance, security badges)

3. **Lead Scoring and Analytics**:
   - Track user engagement metrics (session length, questions asked, CTA clicks)
   - Score leads based on conversation quality and interest indicators
   - Capture qualification information naturally through conversation
   - Integration with CRM/lead management system

**Expected Output**
- Contextual CTA component with intelligent timing
- Lead scoring algorithm integrated into chat context
- Analytics dashboard for sales performance
- Enhanced CTA conversion tracking
- A/B testing framework for CTA optimization

---

## 8. Advanced UX Features and Accessibility **Status:** TODO **Priority:** P1

**Prerequisites**
- All core chat functionality from Stories 4-7.
- Working sales representative behavior.

**Requirements**
1. **Theme and Personalization**:
   - Dark/light theme toggle with system preference detection
   - Font size adjustment for accessibility
   - High contrast mode support
   - Color customization options

2. **Advanced Input Features**:
   - Auto-resize text input area
   - Suggested follow-up questions after each response
   - Quick action buttons for common HSA questions
   - Voice input capability (speech-to-text)

3. **Enhanced Accessibility**:
   - Full keyboard navigation support
   - Screen reader compatibility
   - ARIA labels and semantic markup
   - Focus management for modal dialogs

**Expected Output**
- Theme switching functionality
- Accessibility compliance (WCAG 2.1 AA)
- Voice input integration
- Enhanced keyboard navigation
- Suggested questions component

---

## 9. Add document upload endpoints and OCR service **Status:** TODO **Priority:** P2

**Prerequisites**
- Personal info endpoints exist.
- Chat + CTA flow implemented.

**Requirements**
- Define `DocumentUpload` model and schema.
- Create `backend/api/v1/documents.py`:
    - `POST /documents/upload` → accept files, return task ID.
    - `GET /documents/{id}` → return processing results.
- Implement `document_processor.py` using GPT-4o vision for OCR.
- Store extracted fields in DB.
- Add validation and tests for file limits and OCR output.

**Expected Output**
- Document upload API.
- Processor service integrated with GPT-4o vision.
- Passing tests and updated roadmap.

---

## 10. Implement document upload UI **Status:** TODO **Priority:** P2

**Prerequisites**
- Document upload endpoints are working.

**Requirements**
- Create `DocumentUploadPage`:
    - Upload ID/employer documents with progress bars.
    - Poll backend for OCR results.
    - Display extracted fields for confirmation.
- Add error handling and links back to chat.
- Add tests for upload workflow.

**Expected Output**
- Working upload UI.
- Integrated OCR results display.
- Navigation from personal info → upload.

---

## 11. Build decision engine endpoints **Status:** TODO **Priority:** P2

**Prerequisites**
- Personal info + documents stored in DB.

**Requirements**
- Implement `decision_engine.py`:
    - `evaluate_application(application_id)` → apply rules (expired ID → reject, mismatches → manual review, all valid → approve).
    - Log decisions in audit trail.
- Add `backend/api/v1/decisions.py` with `GET /decisions/{application_id}`.
- Add DB models for decisions and logs.
- Add tests covering all rule branches.

**Expected Output**
- Decision API with audit logs.
- Tests proving rule coverage.

---

## 12. Implement decision screen UI **Status:** TODO **Priority:** P2

**Prerequisites**
- Decision endpoint is live.
- Upload page complete.

**Requirements**
- Create `DecisionPage`:
    - Fetch decision and display approve/reject/manual review.
    - Show rationale and timestamp.
    - Links to restart, return to chat, or contact support.
- Add tests for each outcome.

**Expected Output**
- Functional decision UI.
- End-to-end flow complete.

---

## 13. Ensure memory and roadmap updates **Status:** TODO **Priority:** P2

**Requirements**
- At end of each story:
    - Subagent appends a summary to `PROJECT_ROADMAP.md`.
    - Update `CLAUDE.md` or context files with new rules/configs.
    - Verify memory is refreshed (`/memory`).

**Expected Output**
- Roadmap updated incrementally.
- Context kept in sync.
- Development log consistent.

---

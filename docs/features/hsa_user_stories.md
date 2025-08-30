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

## 3. Implement chatbot UI and CTA **Status:** TODO

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

## 4. Add document upload endpoints and OCR service **Status:** TODO

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

## 5. Implement document upload UI **Status:** TODO

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

## 6. Build decision engine endpoints **Status:** TODO

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

## 7. Implement decision screen UI **Status:** TODO

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

## 8. Ensure memory and roadmap updates **Status:** TODO

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

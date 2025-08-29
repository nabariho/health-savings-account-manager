# User Stories and Acceptance Criteria

This document outlines the business rationale, user stories, and clear acceptance criteria for each major component of the HSA onboarding prototype.  Use these descriptions as a checklist when implementing your solution.

### 1. Data Collection

**Business Reason:**  Collecting essential personal information (full name, date of birth, address, Social Security Number, and employer) is necessary to verify identity and determine eligibility for an HSA.  Financial institutions are required by law to gather this data for Know Your Customer (KYC) and Customer Identification Program (CIP) compliance.

**User Story:**  As an HSA onboarding system, I need to prompt the applicant to enter their personal information so that the institution can verify their identity and eligibility in compliance with regulatory requirements.

**Acceptance Criteria:**

- The system presents input fields for name, date of birth, address, Social Security Number (or simulated ID number), and employer.
- Each field is mandatory.  Attempts to proceed without filling out a required field trigger a clear error message that identifies the missing information.
- The date of birth must be validated as a proper date.  The Social Security Number (or ID number) must match the expected format (for example, nine digits for a U.S. SSN).
- Collected data is stored securely and passed on to the document processing and decisioning modules.

### 2. Document Upload and Processing

**Business Reason:**  Verifying the authenticity of the applicant’s identity and eligibility documents is a critical part of KYC and CIP.  Automated extraction and comparison of document data reduces manual review and deters fraud.

**User Story:**  As the onboarding system, I need to allow users to upload their government ID and proof‑of‑eligibility documents, extract and validate key fields, and determine if they match the user’s provided information so that I can make an informed approval decision.

**Acceptance Criteria:**

- The system accepts uploads of image or PDF files for a government ID and an employer document (proof of eligibility).
- The system uses OCR or an AI vision model to extract the name, date of birth, address, ID number, and expiry date from the ID document.
- The system extracts the applicant name and employer name from the employer document.
- If the ID is expired, the system automatically sets the application status to **Reject**.
- If the extracted name, date of birth, or address does not exactly match the user‑provided data, the system sets the application status to **Manual Review**.
- If all extracted data matches and the ID is valid, the system sets the application status to **Approve**.
- The system gracefully handles unreadable or corrupt files and reports a meaningful error.

### 3. RAG‑Powered FAQs

**Business Reason:**  Applicants frequently ask questions about HSAs.  Using retrieval‑augmented generation (RAG) ensures that responses are accurate and grounded in official documentation, improving user trust and reducing calls to support.

**User Story:**  As the onboarding system, I need to answer users’ questions about HSAs by retrieving relevant information from the supplied IRS documents and composing a concise response so that users can understand the rules and benefits without leaving the onboarding process.

**Acceptance Criteria:**

- The knowledge base is built solely from the provided `HSA_FAQ.txt` and `HSA_Limits.txt` documents.
- When the user asks a question about HSA eligibility, contributions, qualified expenses, or other rules, the system performs a vector search to retrieve relevant passages from the knowledge base.
- The retrieved passages are passed to an LLM (e.g. via the OpenAI API) to generate a concise answer.
- The answer cites the specific document sections (e.g. quotes or paragraph references) used to form the response.
- If the question cannot be answered based on the provided documents, the system returns a polite message indicating that the information is unavailable in the knowledge base.

### 4. Decisioning and Reporting

**Business Reason:**  Automated decisioning provides consistent, transparent outcomes and reduces the burden on human reviewers.  Logging the reasoning behind each decision ensures accountability and facilitates auditing.

**User Story:**  As the onboarding system, I need to compute a risk score and determine an application outcome (Approve / Reject / Manual Review) based on collected data and extracted document information, and I need to log the reasoning so that reviewers can audit the decision.

**Acceptance Criteria:**

- The system defines a set of rules or a scoring algorithm that evaluates ID validity, data matches, and potential risk factors.  For example, expired ID → reject, mismatched information → manual review, all matches → approve.
- The system produces exactly one of three outcomes: **Approve**, **Reject**, or **Manual Review**, along with a brief explanation summarising the key factors (e.g. “ID expired” or “Name mismatch between ID and employer document”).
- The system records the decision, the extracted data, and any mismatches in an audit log or database table.
- Reviewers can access the audit log to see a detailed breakdown of the decision process for each application.

### 5. Deployment and Packaging

**Business Reason:**  Packaging the system for easy local execution and cloud deployment ensures that developers can reproduce results consistently and the solution can be integrated into production environments.

**User Story:**  As a developer, I need the onboarding system packaged in a way that it can be executed locally and containerized for deployment so that I can test and deploy it reliably.

**Acceptance Criteria:**

- The project includes a clear `README` with instructions on how to set up the environment, install dependencies, and run the application locally.
- A `Dockerfile` (and optionally a `docker-compose.yml`) is provided to build and run the system in a containerised environment.
- Configuration values such as API keys and database connections are managed via environment variables or configuration files and are not hard‑coded in the source.
- Running the container starts all necessary services (e.g. the API server and any required databases) and the system behaves as specified in these user stories.


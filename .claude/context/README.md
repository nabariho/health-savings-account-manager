# AI‑Powered HSA Onboarding — Candidate Practice Challenge

## Purpose and Background

This exercise asks you to build a **prototype system** that simulates the experience of opening a Health Savings Account (HSA).  The goal is to demonstrate your ability to design and implement an **agent‑driven AI application** that collects applicant data, processes uploaded documents, answers questions using a knowledge base, and produces a decision (approve, reject or manual review).

Many software engineers may not be familiar with the concept of a Health Savings Account or the regulatory requirements around identity verification.  This section provides a concise introduction so you can understand **why** the system behaves the way it does and what problems it is trying to solve.

### What is an HSA?

An **HSA (Health Savings Account)** is a tax‑advantaged savings account designed to help individuals pay for qualified medical expenses.  In the United States, HSAs are linked to **High‑Deductible Health Plans (HDHPs)** and provide a **triple tax benefit**: contributions are tax‑deductible, growth on the balance is tax‑free, and withdrawals for qualified medical expenses are also tax‑free.  Funds carry over year to year, and the account is portable if the individual changes jobs.

To be eligible to open an HSA, an applicant generally must:

- Be covered by an **HDHP** (as defined by the IRS) and have no other disqualifying health coverage;
- Not be enrolled in Medicare;
- Not be claimed as a dependent on someone else’s tax return;
- Have a valid **Social Security Number** and proof of U.S. residency.

Annual **contribution limits** and **minimum deductible amounts** for HDHPs are set by the IRS and can change each year.  For example, in 2025 the limits on contributions and the minimum deductibles for HDHP coverage will be different from prior years.  These limits and eligibility rules are documented in the official IRS publications provided in the `docs/` folder of this bundle.

### Why do we ask for personal information and documents?

Financial institutions are required to perform **Know Your Customer (KYC)** and **Customer Identification Program (CIP)** checks before opening accounts.  This is to prevent fraud, identity theft and money laundering.  When you open an HSA you will be asked to provide:

1. **Personal data** (full name, date of birth, address, Social Security Number, employer);
2. **Government‑issued photo identification** (such as a driver’s license or passport) to verify your identity and age;
3. **Proof of eligibility**, such as a recent pay stub, employer letter, or health insurance document demonstrating that you are covered by an HDHP.

The system you build should ingest these documents, extract structured information from them using OCR or AI models, and compare the extracted fields against the user’s self‑reported data.  It should also check that the ID has not expired and optionally perform a watch‑list or sanctions lookup.  Based on the extracted data and your rules, the system must decide whether to approve, reject or flag the application for manual review.

### Why do we answer questions?

Applicants often have questions about HSAs, such as **“What expenses are eligible?”**, **“How much can I contribute?”** or **“What happens if I change jobs?”**.  Instead of having them read lengthy legal documents, your system should use **retrieval‑augmented generation (RAG)** to provide grounded answers.  The knowledge base for your RAG implementation is the official IRS documentation included in `docs/`.  When the user asks a question, your system should retrieve relevant passages from the provided publications and feed them into an LLM to generate a concise, accurate response.

### High‑Level Requirements

1. **Data Collection** – Prompt the user for the following fields: full name, date of birth, address, Social Security Number (or simulated ID number), and employer name.  You may implement this as an interactive chatbot, a structured form, or a hybrid.
2. **Document Upload and Processing** – Accept file uploads for a government ID and a proof of eligibility.  Use OCR or an AI vision model to extract key fields from these images/PDFs.  Match the extracted values against the user‑entered data.  Check the ID expiration date and compute a simple risk score.  Based on your rules, return one of three outcomes: **Approve** (everything matches and ID is valid), **Reject** (e.g. ID expired), or **Manual Review** (e.g. name mismatch or poor image quality).
3. **RAG‑Powered FAQs** – Build a small knowledge base from the `docs/` files (`HSA_FAQ.txt` and `HSA_Limits.txt`).  When the user asks general HSA questions, perform a vector search to find relevant passages and produce an answer using an LLM.  Include citations (e.g. short quotes) from the retrieved passages in your answer.
4. **Decisioning and Reporting** – After processing, provide the user with a clear decision (approve/reject/manual review) along with a brief explanation (e.g. “Approved: ID valid and matches all provided data”).  Optionally, produce a risk score and an audit log capturing all steps taken.  Provide a simple admin endpoint or log file where reviewers can inspect flagged cases.
5. **Deployment and Packaging** – Your system must run locally but also be containerized (e.g. via Docker) for easy deployment to the cloud.  Provide a `README` with setup instructions and a design document explaining your architecture, agent roles, and data flow.

### Provided Materials

This bundle contains:

- `docs/` – simplified reference texts derived from IRS publications.  These summarise HSA eligibility, contribution limits and key rules.  **Do not rely on your own knowledge**; your RAG system should retrieve answers from these documents.
- `kyc_samples/` – synthetic sample files for KYC testing.  Each sample includes a placeholder image and a JSON file containing the expected extracted values.  The three scenarios illustrate approve, reject (expired ID) and manual review (data mismatch).  The images are abstract representations of ID cards and employer documents and do not contain real personal data.
- `wireframes/` – a conceptual sketch of a possible user interface.  This is provided to help you visualise a multi‑step onboarding flow.  You may choose to implement a similar UI or adapt it to a fully conversational design.
- `README.md` – this document, which describes the objectives, context and tasks.

### Suggested Approach

To complete this exercise within 20–30 hours:

1. **Design your architecture** – identify the agents or modules you will need.  A typical solution might have separate components for conversation management, document processing, knowledge retrieval and decisioning.
2. **Implement the document pipeline** – start with loading an image file, running OCR and extracting key fields.  Compare the extracted data to the user’s input and determine whether the ID is expired or mismatched.  Assign risk scores accordingly.
3. **Build the knowledge base** – split the provided text files into passages, embed them with a vector model, and implement a simple search to fetch relevant passages based on user questions.  Feed the results into an LLM to produce final answers.
4. **Orchestrate the user experience** – tie together the data collection, document upload and question answering into a coherent flow.  Decide whether you want a chat‑like interface or a form with tooltips and optional chat.
5. **Package and document** – containerize your application, supply instructions for running it, and provide a short design report explaining your key decisions.  Include logs or metrics demonstrating how your system handled the three sample scenarios.

### Caveats and Simplifications

The provided documents and samples are simplified and do not cover every nuance of HSAs.  In a real‑world system, you would need to support additional document types, handle edge cases, and integrate with external APIs (such as watch‑list screening services).  For this exercise, focus on demonstrating your ability to integrate AI techniques (RAG, OCR, agents) into a coherent and testable prototype.  Feel free to make reasonable assumptions and document them clearly.

Good luck!

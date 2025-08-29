# Canonical Requirements
- Treat ./README.md and ./user_stories.md as the contract to fulfill end-to-end.
- Frontend: React + TypeScript + Tailwind CSS.
- Backend: Python API (per README/user_stories).
- Use OpenAI APIs (Responses + Agents SDK) for: Vision/OCR, RAG (with citations), decisioning + audit.
- Outcomes: Approve / Reject / Manual Review.
- Docker: backend + frontend, docker-compose for local.
- Best practices: typed DTOs, tests for decision rules & API contracts, observability, small non-root images.
- Never commit secrets; use env vars.

# kickoff
Use the `software-architect` subagent.
Context: CLAUDE.md, README.md, hsa_user_stories.md, .claude/context/engineering.md.
Goals:
1) Produce ARCHITECTURE.md (modules, data flow, DTOs, API contracts) for:
    - Frontend: React + TypeScript + Tailwind
    - Backend: Python API using OpenAI Responses + Agents SDK
    - Services: OCR/Vision (GPT-4o), RAG (text-embedding-3-large), Decisioning, Audit logging
2) Define folder layout and observability plan; outline Docker/compose plan.
3) Output a TODO list tagged for [feature-dev], [tester], [code-reviewer], [devops].
   Rules:
- Enforce SOLID, KISS, excellent docs.
- DO NOT write application code.
- Append a summary and TODO to PROJECT_ROADMAP.md (create if missing).

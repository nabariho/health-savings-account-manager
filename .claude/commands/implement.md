# implement
Use the `vertical-slice-implementer` subagent.
Context: CLAUDE.md, README.md, user_stories.md, ARCHITECTURE.md, .claude/context/engineering.md.
Goals:
- Implement ONE vertical slice mapped to a user story.
- Frontend: React/TS/Tailwind UI + zod validation + React Query calls.
- Backend: Python API endpoints that call OpenAI (Responses/Agents) per policy.
- RAG stub returns citations; do not hardcode secrets; use env.
  Process:
- Keep commits small (Conventional Commits). Write clear docstrings/TSDoc.
- After edits, automatically hand off to `tester` to add/run tests; iterate until green.
- Append slice summary (files touched, tests added) to PROJECT_ROADMAP.md.
  Do not bypass standards or hooks; prefer simplest design that passes all tests.

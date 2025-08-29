# test
Use the `test-generator-from-stories` subagent.
Context: user_stories.md, README.md, ARCHITECTURE.md, .claude/context/engineering.md.
Goals:
- Derive tests for decision rules:
    - Expired ID → Reject
    - Mismatch → Manual Review
    - All valid → Approve
- API contract tests + RAG grounding (answers include citations).
- Run tests; summarize failures; propose minimal patches to `feature-dev`.
- Update PROJECT_ROADMAP.md with what passed/failed and coverage highlights.
  Rules: keep tests readable; document intent; do not commit secrets.

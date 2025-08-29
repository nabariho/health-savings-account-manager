# Contributing

## Workflow
1) Create a small, focused branch per user story.
2) Commit using **Conventional Commits** (e.g., `feat(ui): add upload step`).
3) Open a PR early; keep it small; include tests.
4) Require at least one approval; squash-merge with a clean message.

## Commit Messages
Follow the Conventional Commits spec:
`<type>(optional scope): <short imperative>`
Types: feat, fix, docs, refactor, test, chore, build, ci, perf.
Ref: conventionalcommits.org . 

## Pull Requests
Small, single-purpose PRs are faster to review/merge and reduce risk (GitHub guidance).

## Code Standards
- **SOLID** + **KISS** for design.
- **TypeScript**: TSDoc/JSDoc for exported APIs.
- **Python**: clear docstrings (Google or NumPy style).
- Tests for decision rules, API contracts, and RAG citations.

## Secrets
No secrets in code or history. Use env vars like `OPENAI_API_KEY`.

# Engineering Standards

## Design & Code Quality
- Apply **SOLID** principles for maintainable, testable modules.
- Apply **KISS**: prefer the simplest solution that satisfies requirements; avoid needless abstractions.
- Keep functions small; isolate side effects; favor composition.
- Strong typing: TypeScript interfaces/types; Python Pydantic models where appropriate.

## Documentation
- **TypeScript**: use TSDoc/JSDoc-style comments for exported symbols; include params/returns and 1–2 line intent.
- **Python**: use docstrings (Google or NumPy style). Document side effects, exceptions, and I/O.
- Update README/ARCHITECTURE/testing notes when behavior or interfaces change.

## Git & Review Process
- **Conventional Commits** for history clarity (feat, fix, docs, refactor, test, chore, build, ci, perf).
- Keep commits **small and focused**. Each PR covers **one** unit of work and includes tests.
- Require at least **one human approval** before merge.

## Testing & CI
- Tests for decision rules, API contracts, and critical paths.
- RAG answers must include **citations** for traceability.
- Lint/format must pass pre-merge.

## Security & Secrets
- No secrets in code or history; use env vars (e.g., OPENAI_API_KEY). Never commit `.env*` or `secrets/**`.

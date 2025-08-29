# review
Use the `code-diff-reviewer` subagent.
Context: .claude/context/engineering.md, CLAUDE.md, recent diffs.
Goals:
- Review last commit(s)/PR diff for correctness, security, performance, readability.
- Output: Critical → Warnings → Suggestions, with concrete patch diffs.
- Verify: SOLID/KISS, TSDoc/docstrings, small focused commits, Conventional Commits, tests present, no secrets/PII.
- Write a short review note to PROJECT_ROADMAP.md.

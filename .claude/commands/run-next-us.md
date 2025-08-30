# run-next-us
Goal: Execute one user story end-to-end with small commits and a PR.

Context:
- CLAUDE.md
- docs/features/hsa_user_stories.md
- ARCHITECTURE.md
- .claude/context/engineering.md

Steps for the `software-architect` + `vertical-slice-implementer` + `test-generator-from-stories` + `code-diff-reviewer` + `docker-containerization-specialist` subagents:

1) SELECT STORY
- Run: `python3 scripts/select_next_us.py`
- Parse JSON: {title, slug}. If title is null, STOP and report "No TODO stories".
- Create a short plan. Confirm affected modules.

2) BRANCH
- Branch name: `feature/us-${slug}`
- Run bash:
    - `git checkout -b feature/us-${slug}`
    - `git push -u origin feature/us-${slug}`

3) ARCHITECTURE (software-architect)
- If the story is a design story, produce the specified doc and update `/docs/architecture/...`.
- Otherwise, validate existing contracts and update `ARCHITECTURE.md` only if needed.
- Append a “Planned changes” note to PROJECT_ROADMAP.md.

4) IMPLEMENT (vertical-slice-implementer)
- Implement the smallest vertical slice that satisfies this story.
- Enforce SOLID, KISS, and excellent docs (per .claude/context/engineering.md).
- Never commit secrets. Keep commits small (Conventional Commits).
- After edits, hand off to `tester`.

5) TEST (test-generator-from-stories)
- Generate/expand tests derived from the story’s acceptance criteria.
- Run tests. If failures, propose minimal patches and iterate with `feature-dev` until green.

6) REVIEW (code-diff-reviewer)
- Review diffs for correctness, security, performance, readability, and standards.
- Provide Critical / Warnings / Suggestions with minimal patch diffs.
- Apply safe patches if needed.

7) DEVOPS (docker-containerization-specialist)
- If new endpoints/services were added, update Dockerfile(s) + docker-compose.
- Ensure env_file: .env for API. Add /health if missing.
- Verify `docker compose up --build` locally.

8) PUSH & PR
- Run:
    - `git add -A && git commit -m "feat(us): implement ${title}"`
    - `git push`
    - `gh pr create --fill --head feature/us-${slug} --title "feat(us): ${title}" --body "Implements: ${title}\n\n- [x] Arch\n- [x] Dev\n- [x] Test\n- [x] Review\n- [x] DevOps"`
- Post the PR URL in the response.

9) DOCUMENT & MARK DONE
- Update PROJECT_ROADMAP.md with what was shipped (endpoints, UI, tests, known gaps).
- In docs/features/hsa_user_stories.md, change the story’s status to `**Status:** DONE`.
- If new follow-ups emerged, append them as new stories with `**Status:** TODO`.

Rules:
- Always obey .claude/context/engineering.md (SOLID, KISS, docs, Conventional Commits, PR-before-merge).
- Keep changes small and reviewable. If scope grows, split and open follow-up stories.

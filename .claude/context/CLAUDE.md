# Project Memory for Claude Code
This repository’s product contract and implementation rules must always be considered.

## Canonical docs (imported)
@README.md
@user_stories.md
@.claude/context/requirements.md
@.claude/context/openai.md

## Instructions to all subagents
- Obey the imported docs as the source of truth.
- Frontend must be React + TypeScript + Tailwind.
- Backend must be a Python API; prefer OpenAI Responses/Agents for LLM work.
- Produce tests, code review notes, and Docker packaging as part of each slice.
- Never read `.env*` or `secrets/**`; treat secrets as environment variables only.

@.claude/context/engineering.md
